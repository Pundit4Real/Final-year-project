from django.urls import path

urlpatterns = [
    # Add at least one dummy or real path
    path('test/', lambda request: HttpResponse("Test successful")),
]
