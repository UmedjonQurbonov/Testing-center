from django.db import models
from django.utils import timezone


class Cluster(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Subject(models.Model):
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE, related_name="subjects")
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Question(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()

    def __str__(self):
        return self.text[:50]


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text



class TestResult(models.Model):
    user = models.ForeignKey("accounts.CustomUser", on_delete=models.CASCADE)
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    score = models.IntegerField()
    total = models.IntegerField()
    attempt = models.IntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.cluster.name} - {self.score}"


class UserAnswer(models.Model):
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name="user_answers")
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    answer = models.ForeignKey("Answer", on_delete=models.CASCADE)
    is_correct = models.BooleanField()

    def __str__(self):
        return f"{self.question.text[:20]} - {self.answer.text}"
