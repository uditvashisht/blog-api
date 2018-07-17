from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.contenttypes.models import ContentType

from .models import Comment
from .forms import CommentForm

# Create your views here.


@login_required
def comment_delete(request, pk):
    # object = get_object_or_404(Comment, pk=pk)

    try:
        object = Comment.objects.get(pk=pk)
    except:
        raise Http404

    if object.user != request.user:
        # raise Http404
        response = HttpResponse("You do not have permission to delete it.")
        response.status_code = 403
        return response

    if request.POST:
        parent_object_url = object.content_object.get_absolute_url()

        object.delete()
        return HttpResponseRedirect(parent_object_url)
    context = {
        "object": object,
    }

    return render(request, "confirm_delete.html", context)


def comment_thread(request, pk):

    # object = get_object_or_404(Comment, pk=pk)

    try:
        object = Comment.objects.get(pk=pk)
    except:
        raise Http404

    if not object.is_parent:
        object = object.parent

    content_object = object.content_object
    content_pk = object.content_object.pk

    initial_data = {
        "content_type": object.content_type,
        "object_pk": object.object_pk,
    }
    form = CommentForm(request.GET or None, initial=initial_data)

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

    context = {
        "comment": object,
        "form": form

    }
    return render(request, 'comment_thread.html', context)
