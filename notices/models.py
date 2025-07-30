from django.db import models
from django.utils import timezone

# Create your models here.
class NoticeCategory(models.Model):
    """공지사항 대분류 (공지사항, 곰나루광장)"""
    name = models.CharField(max_length=100, verbose_name="카테고리명")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "공지사항 카테고리"
        verbose_name_plural = "공지사항 카테고리"
    
    def __str__(self):
        return self.name
    
class NoticeBoard(models.Model):
    """각 카테고리의 게시판 (학생소식, 행정소식 등)"""
    category = models.ForeignKey(NoticeCategory, on_delete=models.CASCADE, related_name="boards")
    name = models.CharField(max_length=100, verbose_name="게시판명")
    url = models.URLField(verbose_name="게시판 URL")
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "공지사항 게시판"
        verbose_name_plural = "공지사항 게시판"

    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
class Notice(models.Model):
    """실제 공지사항 데이터"""
    board = models.ForeignKey(NoticeBoard, on_delete=models.CASCADE, related_name="notices")
    title = models.CharField(max_length=500, verbose_name="제목")
    url = models.URLField(verbose_name="공지사항 URL")
    author = models.CharField(max_length=100, verbose_name="작성자", blank=True, null=True)
    published_date = models.DateField(verbose_name="게시일")
    view_count = models.IntegerField(default=0, verbose_name="조회수", blank=True, null=True)
    is_important = models.BooleanField(default=False, verbose_name="중요공지")

    # 메카 정보
    crawled_at = models.DateTimeField(auto_now_add=True, verbose_name="크롤링 시간")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정시간")

    class Meta:
        verbose_name = "공지사항"
        verbose_name_plural = "공지사항"
        ordering = ['-published_date', '-crawled_at']
        unique_together = ['board', 'url']

    def __str__(self):
        return f"[{self.board.name}] {self.title[:50]}"