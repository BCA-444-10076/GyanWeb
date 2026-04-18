from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from head.models import createUser, uploadQuestion
from .models import UserAnswer, InterviewResult, StudentMarks, InterviewSession
from .serializers import StudentLoginSerializer, AnswerSerializer, QuestionViewSerializer
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .utils.ai_evaluator import evaluate_answer
from django.db.models import Sum


def student_login_required(view_func):
    """Custom decorator to check if student is logged in via session"""
    def wrapper(request, *args, **kwargs):
        # Check if user is logged in via session
        user_id = request.session.get('student_user_id')
        if not user_id:
            # If no user_id in session, redirect to login
            return redirect('/student/login/?next=' + request.path)
        
        # Verify user exists
        try:
            user = createUser.objects.get(userId=user_id)
            request.current_student = user
            return view_func(request, *args, **kwargs)
        except createUser.DoesNotExist:
            # Clear invalid session and redirect to login
            if 'student_user_id' in request.session:
                del request.session['student_user_id']
            return redirect('/student/login/?next=' + request.path)
    
    return wrapper


def login_page(request):
    return render(request, 'student/login.html')

@student_login_required
def start_exam_page(request):
    # Get user data from session
    user_id = request.session.get('student_user_id')
    user_data = None
    
    if user_id:
        try:
            from head.models import createUser
            user = createUser.objects.get(userId=user_id)
            user_data = {
                'userName': user.userName,
                'userId': user.userId
            }
        except createUser.DoesNotExist:
            pass
    
    return render(request, 'student/startExam.html', {'user': user_data})

@student_login_required
def test_page(request):
    user_id = request.session.get('student_user_id')
    user_data = None

    if user_id:
        try:
            user = createUser.objects.get(userId=user_id)
            user_data = {
                'userName': user.userName,
                'userId': user.userId
            }
        except createUser.DoesNotExist:
            pass

    return render(request, 'student/test.html', {'user': user_data})

@student_login_required
def thankyou_page(request):
    # Get user data from session
    user_id = request.session.get('student_user_id')
    user_data = None
    
    if user_id:
        try:
            from head.models import createUser
            user = createUser.objects.get(userId=user_id)
            user_data = {
                'userName': user.userName,
                'userId': user.userId
            }
        except createUser.DoesNotExist:
            pass
    
    # Check if student came from interview (by checking HTTP referer or a parameter)
    from_interview = request.GET.get('from_interview') == 'true'
    
    # Also check if user has completed interview
    if user_id and not from_interview:
        try:
            from .models import InterviewResult
            interview_completed = InterviewResult.objects.filter(user__userId=user_id).exists()
            if interview_completed:
                from_interview = True
        except:
            pass
    
    return render(request, 'student/thankyou.html', {
        'user': user_data,
        'from_interview': from_interview
    })

@student_login_required
def logout_view(request):
    """Clear student session and redirect to login"""
    # Clear session data
    if 'student_user_id' in request.session:
        del request.session['student_user_id']
    request.session.save()
    
    return redirect('/student/login/')

@student_login_required
def student_result_page(request):
    return render(request, 'student/studentResult.html')

@method_decorator(csrf_exempt, name='dispatch')
class UserLogin(APIView):
    def post(self, request):
        try:
            serializer = StudentLoginSerializer(data=request.data)
            if serializer.is_valid():
                uid = serializer.validated_data['id']
                pwd = serializer.validated_data['password']
                print("Login attempt with ID:", uid, "| Password:", pwd)

                from head.models import createUser
                try:
                    user = createUser.objects.get(userId=uid, userPassword=pwd)
                    
                    print("Login Success:", user.userName)
                    
                    # Store user ID in session
                    request.session['student_user_id'] = user.userId
                    request.session.save()
                    
                    return Response({
                        'message': 'Login successful',
                        'userName': user.userName,
                        'userId': user.userId
                    }, status=status.HTTP_200_OK)

                except createUser.DoesNotExist:
                    print("No match found for:", uid, pwd)
                    return Response({'error': 'Invalid student ID or password'}, status=status.HTTP_401_UNAUTHORIZED)

            else:
                print("Serializer error:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print("Exception in UserLogin:", str(e))
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class SubmitAnswer(APIView):
    def post(self, request):
        serializer = AnswerSerializer(data=request.data)
        if serializer.is_valid():
            question_id = serializer.validated_data['question_id']
            user_id = serializer.validated_data['user_id']
            answer_text = serializer.validated_data['answer_text']

            try:
                question = uploadQuestion.objects.get(id=question_id)
                user = createUser.objects.get(userId=user_id)

                marks = evaluate_answer(question.question, answer_text, question.marks)
                UserAnswer.objects.create(user=user, question=question, answer_text=answer_text, marks=marks)

                # Recalculate and update total marks
                total_marks = UserAnswer.objects.filter(user=user).aggregate(total=Sum('marks'))['total'] or 0
                StudentMarks.objects.update_or_create(user=user, defaults={"marks": total_marks})

                return Response({'message': 'Answer submitted and evaluated', 'marks': marks}, status=status.HTTP_201_CREATED)

            except uploadQuestion.DoesNotExist:
                return Response({'error': 'Invalid question ID'}, status=status.HTTP_400_BAD_REQUEST)
            except createUser.DoesNotExist:
                return Response({'error': 'Invalid user ID'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ViewQuestion(APIView):
    def get(self, request):
        question_id = request.query_params.get('id')
        if question_id:
            try:
                question = uploadQuestion.objects.get(id=question_id)
                serializer = QuestionViewSerializer(question)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except uploadQuestion.DoesNotExist:
                return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'error': 'Please provide a question ID'}, status=status.HTTP_400_BAD_REQUEST)

class GetAllQuestions(APIView):
    def get(self, request):
        questions = uploadQuestion.objects.all()
        data = [{"id": q.id} for q in questions]
        return Response(data)

@method_decorator(csrf_exempt, name='dispatch')
class SaveInterviewQA(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")
        question = request.data.get("question")
        answer = request.data.get("answer")

        try:
            user = createUser.objects.get(userId=user_id)
            InterviewSession.objects.create(user=user, question=question, answer=answer)
            return Response({"message": "Saved"}, status=201)
        except createUser.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

@method_decorator(csrf_exempt, name='dispatch')
class SaveInterviewResult(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")
        result = request.data.get("result_summary")

        try:
            user = createUser.objects.get(userId=user_id)
            InterviewResult.objects.update_or_create(
                user=user,
                defaults={'result_summary': result}
            )
            return Response({"message": "Result saved"}, status=201)
        except createUser.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

@student_login_required
def interview_page(request):
    user_id = request.session.get('student_user_id')
    user_data = None

    if user_id:
        try:
            user = createUser.objects.get(userId=user_id)
            user_data = {
                'userName': user.userName,
                'userId': user.userId
            }
        except createUser.DoesNotExist:
            pass

    return render(request, 'student/interview.html', {'user': user_data})

@api_view(['GET'])
def get_student_answers(request):
    user_id = request.GET.get("id")
    try:
        user = createUser.objects.get(userId=user_id)
        answers = UserAnswer.objects.filter(user=user).select_related('question')
        
        data = []
        for a in answers:
            if a.question:  # Safety check
                data.append({
                    "question": a.question.question or "",
                    "answer": a.answer_text or "",
                    "question_id": a.question.id,
                    "marks": a.marks or 0,
                    "max_marks": a.question.marks or 10
                })
        
        return Response({"answers": data})
    except createUser.DoesNotExist:
        return Response({"error": "User not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def save_student_marks(request):
    user_id = request.data.get("user_id")
    total_marks = request.data.get("total_marks")
    marks_data = request.data.get("marks", [])

    try:
        user = createUser.objects.get(userId=user_id)
        
        # Update individual UserAnswer records
        from .models import UserAnswer
        for mark_data in marks_data:
            question_id = mark_data.get("question_id")
            marks = mark_data.get("marks")
            
            try:
                user_answer = UserAnswer.objects.get(user=user, question_id=question_id)
                user_answer.marks = marks
                user_answer.save()
            except UserAnswer.DoesNotExist:
                # Create if doesn't exist
                from head.models import uploadQuestion
                question = uploadQuestion.objects.get(id=question_id)
                UserAnswer.objects.create(user=user, question=question, marks=marks, answer_text="")
        
        # Calculate total possible marks for this student
        user_answers = UserAnswer.objects.filter(user=user).select_related('question')
        total_possible_marks = sum(answer.question.marks for answer in user_answers if answer.question)
        
        # Calculate and save grade using the same logic as head views
        from head.views import calculate_grade
        grade = calculate_grade(total_marks, total_possible_marks)
        
        # Update StudentMarks with new total and grade
        StudentMarks.objects.update_or_create(
            user=user, 
            defaults={
                "marks": total_marks,
                "grade": grade
            }
        )
        
        return Response({
            "message": "Marks saved successfully",
            "grade": grade,
            "total_marks": total_marks
        })
    except createUser.DoesNotExist:
        return Response({"error": "User not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
def get_interview_transcript(request):
    user_id = request.GET.get("user_id")

    try:
        user = createUser.objects.get(userId=user_id)
        qa = InterviewSession.objects.filter(user=user).values("question", "answer")
        result = InterviewResult.objects.filter(user=user).first()

        return Response({
            "qa": list(qa),
            "result_summary": result.result_summary if result else ""
        })

    except createUser.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

@api_view(['GET'])
def get_student_result(request):
    user_id = request.GET.get("user_id")
    try:
        user = createUser.objects.get(userId=user_id)
        marks_obj = StudentMarks.objects.filter(user=user).first()
        interview_result = InterviewResult.objects.filter(user=user).first()
        
        # Calculate total possible marks from user's answers
        from .models import UserAnswer
        user_answers = UserAnswer.objects.filter(user=user).select_related('question')
        total_possible_marks = sum(answer.question.marks for answer in user_answers if answer.question)

        return Response({
            "marks": marks_obj.marks if marks_obj else 0,
            "grade": marks_obj.grade if marks_obj else None,
            "total_possible_marks": total_possible_marks,
            "result_summary": interview_result.result_summary if interview_result else None
        })

    except createUser.DoesNotExist:
        return Response({"error": "User not found"}, status=404)
