from django.shortcuts import render
from django.views.decorators.http import require_http_methods
# Create your views here.
@require_http_methods(["POST"])
def create_post(request):
    raise NotImplementedError("Create post functionality is not implemented yet")

@require_http_methods(["GET"])
def get_post(request):
    raise NotImplementedError("Get post functionality is not implemented yet")

@require_http_methods(["PUT"])
def update_post(request):
    raise NotImplementedError("Update post functionality is not implemented yet")

@require_http_methods(["DELETE"])
def delete_post(request):
    raise NotImplementedError("Delete post functionality is not implemented yet")

@require_http_methods(["GET"])
def list_posts(request):
    raise NotImplementedError("List posts functionality is not implemented yet")

@require_http_methods(["POST"])
def like_post(request):
    raise NotImplementedError("Like post functionality is not implemented yet")

@require_http_methods(["POST"])
def favorite_post(request):
    raise NotImplementedError("Favorite post functionality is not implemented yet")

@require_http_methods(["POST"])
def review_post(request):
    raise NotImplementedError("Review post functionality is not implemented yet")   

@require_http_methods(["POST"])
def reply_review(request):
    raise NotImplementedError("Reply review functionality is not implemented yet")

@require_http_methods(["POST"])
def report_post(request):
    raise NotImplementedError("Report post functionality is not implemented yet")

@require_http_methods(["POST"])
def share_post(request):
    raise NotImplementedError("Share post functionality is not implemented yet")


