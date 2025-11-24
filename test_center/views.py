from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Sum 
from django.utils import timezone
from .models import Cluster, Subject, Question, Answer, TestResult
import random
from collections import defaultdict

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
    completed_attempts = user_results.values('attempt').annotate(
        subject_count=Count('subject', distinct=True)
    ).filter(subject_count=cluster.subjects.count())

    last_completed = completed_attempts.order_by('-attempt').first()
    last_completed_num = last_completed['attempt'] if last_completed else 0

    if request.GET.get("retry"):
        current_attempt = last_completed_num + 1
    else:
        current_attempt = last_completed_num + 1

    completed_in_current = user_results.filter(attempt=current_attempt).values_list('subject_id', flat=True)
    all_completed = len(completed_in_current) == subjects.count()

    context = {
        "cluster": cluster,
        "subjects": subjects,
        "user_results": user_results,
        "current_attempt": current_attempt,
        "completed_in_current": completed_in_current,
        "completed_count": len(completed_in_current),
        "total_subjects": subjects.count(),
        "all_completed": all_completed,
    }
    return render(request, "subjects_list.html", context)

@login_required
def start_test(request, cluster_id, subject_id):
    cluster = get_object_or_404(Cluster, id=cluster_id)
    subject = get_object_or_404(Subject, id=subject_id, cluster=cluster)

    user_results = TestResult.objects.filter(user=request.user, cluster=cluster)

    completed_attempts = user_results.values('attempt').annotate(
        subject_count=Count('subject', distinct=True)
    ).filter(subject_count=cluster.subjects.count())

    last_completed = completed_attempts.order_by('-attempt').first()
    attempt_num = (last_completed['attempt'] if last_completed else 0) + 1

    if user_results.filter(subject=subject, attempt=attempt_num).exists():
        return redirect("subjects_list", cluster_id=cluster.id)

    questions = []
    for q in subject.questions.all():
        answers = list(q.answers.all())
        random.shuffle(answers)
        questions.append({"question": q, "answers": answers})

    return render(request, "start_test.html", {
        "cluster": cluster,
        "subject": subject,
        "questions": questions, 
        "attempt": attempt_num,
    })

@login_required
def finish_test(request, cluster_id, subject_id):
    if request.method != "POST":
        return redirect("start_test", cluster_id=cluster_id, subject_id=subject_id)

    cluster = get_object_or_404(Cluster, id=cluster_id)
    subject = get_object_or_404(Subject, id=subject_id, cluster=cluster)
    attempt = int(request.POST.get("attempt", 1))

    score = 0
    for q in subject.questions.all():
        selected = request.POST.get(f"q_{q.id}")
        if selected:
            try:
                ans = Answer.objects.get(id=selected, question=q)
                if ans.is_correct:
                    score += 1
            except:
                pass

    TestResult.objects.create(
        user=request.user,
        cluster=cluster,
        subject=subject,
        score=score,    
        total=subject.questions.count(),
        attempt=attempt,
    )

    return redirect("subjects_list", cluster_id=cluster.id)

@login_required
def attempts_history(request, cluster_id):
    cluster = get_object_or_404(Cluster, id=cluster_id)
    results = TestResult.objects.filter(
        user=request.user, cluster=cluster
    ).select_related('subject').order_by('-attempt', '-created_at')

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