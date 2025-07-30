from django.db import models
from django.utils import timezone

# Create your models here.
class NoticeCategory(models.Model):
    """공지사항 대분류 (공지사항, 곰나루광장)"""
    name = models.CharField(max_length=100, verbose_name="카테고리명")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
class NoticeBoard(models.Model):
    """각 카테고리의 게시판 (학생소식, 행정소식 등)"""
    category = models.ForeignKey(NoticeCategory, on_delete=models.CASCADE, related_name="boards")
    name = models.CharField(max_length=100)
    url = models.URLField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class Notice(models.Model):
    """실제 공지사항 데이터"""
    board = models.ForeignKey(NoticeBoard, on_delete=models.CASCADE, related_name="notices")
    title = models.CharField(max_length=200)
    url = models.URLField()
    published_date = models.DateField()
    display_order = models.IntegerField(default=0)
    crawled_at = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=100, blank=True, null=True)
    view_count = models.IntegerField(default=0)
    is_important = models.BooleanField(default=False)    

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title