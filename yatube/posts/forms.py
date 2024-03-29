from django import forms
from .models import Post, Comment
from django.core.exceptions import ValidationError


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': ('Текст поста'),
            'group': ('Группа поста')
        }
        help_texts = {
            'text': ('Введите текст поста'),
            'group': ('Выберите группу поста (опционально)')
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': ('Комментарий')}

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == '':
            raise ValidationError
        return data
