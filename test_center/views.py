# test_center/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import random

from .models import (
    Cluster, Subject, Question, Answer,
    TestResult, ActiveTestSession
)


# Главная страница
def index(request):
    clusters = Cluster.objects.all()
    return render(request, "home.html", {"clusters": clusters})


@login_required
def clusters_list(request):
    clusters = Cluster.objects.all()
    return render(request, "clusters_list.html", {"clusters": clusters})


@login_required
def subjects_list(request, cluster_id):
    cluster = get_object_or_404(Cluster, id=cluster_id)
    subjects = cluster.subjects.all()
    user_results = TestResult.objects.filter(user=request.user, cluster=cluster)

    # Определяем текущую попытку
    completed_attempts = user_results.values('attempt').annotate(
        subject_count=Count('subject', distinct=True)
    ).filter(subject_count=cluster.subjects.count())

    last_completed = completed_attempts.order_by('-attempt').first()
    last_attempt_num = last_completed['attempt'] if last_completed else 0
    current_attempt = last_attempt_num + 1

    # Сколько предметов сдано в текущей попытке
    completed_in_current = user_results.filter(attempt=current_attempt).values_list('subject_id', flat=True)
    all_completed = len(completed_in_current) == subjects.count()

    context = {
        "cluster": cluster,
        "subjects": subjects,
        "current_attempt": current_attempt,
        "completed_count": len(completed_in_current),
        "total_subjects": subjects.count(),
        "all_completed": all_completed,
    }
    return render(request, "subjects_list.html", context)


@login_required
def start_test(request, cluster_id, subject_id):
    cluster = get_object_or_404(Cluster, id=cluster_id)
    subject = get_object_or_404(Subject, id=subject_id, cluster=cluster)

    # Ҳисоб кардани attempt
    user_results = TestResult.objects.filter(user=request.user, cluster=cluster)
    completed_attempts = user_results.values('attempt').annotate(
        subject_count=Count('subject', distinct=True)
    ).filter(subject_count=cluster.subjects.count())
    last_completed = completed_attempts.order_by('-attempt').first()
    attempt_num = (last_completed['attempt'] if last_completed else 0) + 1

    if TestResult.objects.filter(user=request.user, subject=subject, attempt=attempt_num).exists():
        return redirect("subjects_list", cluster_id=cluster.id)

    session, created = ActiveTestSession.objects.get_or_create(
        user=request.user,
        cluster=cluster,
        subject=subject,
        attempt=attempt_num,
        defaults={'started_at': timezone.now()}
    )

    # Агар вақт тамом шуд (масалан 2 соат)
    if (timezone.now() - session.started_at).total_seconds() > 7200:
        return redirect('finish_test', cluster_id=cluster.id, subject_id=subject.id)

    # МУҲИМ: ҲАМОН СТРУКТУРАИ ПЕШТАРА — list of dicts!
    questions = []
    for q in subject.questions.prefetch_related('answers').all():
        answers = list(q.answers.all())
        random.shuffle(answers)
        questions.append({
            "question": q,
            "answers": answers    # <— ИН ДУРУСТ АСТ!
        })

    return render(request, "start_test.html", {
        "cluster": cluster,
        "subject": subject,
        "questions": questions,           # list[dict] — дуруст!
        "attempt": attempt_num,
        "session_id": session.id,
        "current_index": session.current_question_index,
    })

@login_required
@require_POST
def finish_test(request, cluster_id, subject_id):
    cluster = get_object_or_404(Cluster, id=cluster_id)
    subject = get_object_or_404(Subject, id=subject_id, cluster=cluster)
    attempt = int(request.POST.get("attempt", 1))

    # Получаем сессию (если есть)
    try:
        session = ActiveTestSession.objects.get(
            user=request.user,
            cluster=cluster,
            subject=subject,
            attempt=attempt
        )
        saved_answers = session.answers
        session.delete()  # Удаляем сессию после завершения
    except ActiveTestSession.DoesNotExist:
        saved_answers = {}

    score = 0
    total = subject.questions.count()

    # Подсчёт правильных ответов
    for question in subject.questions.all():
        selected_id = request.POST.get(f"q_{question.id}") or saved_answers.get(str(question.id))
        if selected_id:
            try:
                answer = Answer.objects.get(id=int(selected_id), question=question)
                if answer.is_correct:
                    score += 1
            except (Answer.DoesNotExist, ValueError):
                pass

    # Сохраняем результат
    TestResult.objects.create(
        user=request.user,
        cluster=cluster,
        subject=subject,
        score=score,
        total=total,
        attempt=attempt,
    )

    return redirect("subjects_list", cluster_id=cluster.id)


@login_required
def attempts_history(request, cluster_id):
    cluster = get_object_or_404(Cluster, id=cluster_id)
    results = TestResult.objects.filter(
        user=request.user, cluster=cluster
    ).select_related('subject').order_by('-attempt', '-created_at')

    from collections import defaultdict
    attempts = defaultdict(lambda: {
        'results': [], 'total_score': 0, 'total_questions': 0,
        'subjects': set(), 'last_date': None, 'completed': False
    })

    for r in results:
        a = attempts[r.attempt]
        a['results'].append(r)
        a['total_score'] += r.score
        a['total_questions'] += r.total
        a['subjects'].add(r.subject_id)
        if not a['last_date'] or r.created_at > a['last_date']:
            a['last_date'] = r.created_at

    for num, data in attempts.items():
        if len(data['subjects']) == cluster.subjects.count():
            data['completed'] = True

    sorted_attempts = dict(sorted(attempts.items(), key=lambda x: x[0], reverse=True))

    return render(request, "attempts_history.html", {
        "cluster": cluster,
        "attempts": sorted_attempts,
        "total_subjects": cluster.subjects.count(),
    })


@login_required
def cluster_result(request, cluster_id):
    cluster = get_object_or_404(Cluster, id=cluster_id)
    results = TestResult.objects.filter(user=request.user, cluster=cluster)

    if results.count() != cluster.subjects.count():
        return redirect("subjects_list", cluster_id=cluster_id)

    total_score = sum(r.score for r in results)
    total_questions = sum(r.total for r in results)

    return render(request, "cluster_result.html", {
        "cluster": cluster,
        "results": results,
        "total_score": total_score,
        "total_questions": total_questions,
    })


# ——— AJAX для сохранения прогресса и ответов ———

@csrf_exempt
@require_POST
@login_required
def save_answer(request):
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        question_id = data.get('question_id')
        answer_id = data.get('answer_id')

        session = ActiveTestSession.objects.get(id=session_id, user=request.user)
        session.answers[str(question_id)] = answer_id
        session.save()
        return JsonResponse({"status": "saved"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@csrf_exempt
@require_POST
@login_required
def update_progress(request):
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        current_index = int(data.get('current_index', 0))

        session = ActiveTestSession.objects.get(id=session_id, user=request.user)
        session.current_question_index = current_index
        session.save()
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)