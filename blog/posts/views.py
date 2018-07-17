from urllib.parse import quote
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404, redirect

from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q

from django.contrib.contenttypes.models import ContentType

from comments.models import Comment
from comments.forms import CommentForm
from .models import Post
from .forms import PostForm


# Create your views here.


def posts_create(request):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.user = request.user
        instance.save()
        messages.success(request, "Success")
        return HttpResponseRedirect(instance.get_absolute_url())

    context = {
        'form': form,
    }
    return render(request, 'post_form.html', context)


def posts_detail(request, slug):
    instance = get_object_or_404(Post, slug=slug)
    if instance.draft or instance.publish > timezone.now().date():
        if not request.user.is_staff or not request.user.is_superuser:
            raise Http404
    share_string = quote(instance.title)

    # to show the comments and save them
    initial_data = {
        "content_type": instance.get_content_type,
        "object_pk": instance.pk
    }
    form = CommentForm(request.POST or None, initial=initial_data)
    if form.is_valid() and request.user.is_authenticated:
        c_type = form.cleaned_data.get("content_type")
        content_type = ContentType.objects.get(model=c_type)
        object_pk = form.cleaned_data.get('object_pk')
        content_data = form.cleaned_data.get("content")
        parent_object = None

        try:
            parent_pk = int(request.POST.get("parent_pk"))
            # print("Parent Id is ", parent_id)
        except:
            parent_pk = None

        if parent_pk:
            parent_qs = Comment.objects.filter(pk=parent_pk)
            if parent_qs.exists():  # and parent_qs.count == 1:
                parent_object = parent_qs.first()

        new_comment, created = Comment.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_pk=object_pk,
            content=content_data,
            parent=parent_object,
        )
        return HttpResponseRedirect(new_comment.content_object.get_absolute_url())
    # comments stuff ends here

    # comments is the property in post model
    comments = instance.comments
    context = {
        'instance': instance,
        'share_string': share_string,
        'comments': comments,
        'comment_form': form,

    }
    return render(request, 'post_detail.html', context)


def posts_list(request):
    today = timezone.now().date()
    post_list = Post.objects.active()
    if request.user.is_staff or request.user.is_superuser:
        post_list = Post.objects.all()

    query = request.GET.get('q')
    if query:
        post_list = post_list.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        ).distinct()
    paginator = Paginator(post_list, 3)  # Show 3 posts per page

    page = request.GET.get('page')
    posts = paginator.get_page(page)

    context = {
        'posts': posts,
        'today': today,
    }
    return render(request, 'post_list.html', context)


def posts_update(request, slug):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    instance = get_object_or_404(Post, slug=slug)
    form = PostForm(request.POST or None, request.FILES or None, instance=instance)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        messages.success(request, "Success")
        return HttpResponseRedirect(instance.get_absolute_url())

    context = {
        'instance': instance,
        'form': form,
    }
    return render(request, 'post_form.html', context)


def posts_delete(request, slug):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    instance = get_object_or_404(Post, slug=slug)
    instance.delete()
    messages.success(request, 'deleted')
    return redirect('posts:list')
