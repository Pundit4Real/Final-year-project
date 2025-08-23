from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls.static import static


schema_view = get_schema_view(
   openapi.Info(
      title="Blockchain Voting System API",
      default_version='v1',
      description="API documentation for Blockchain Voting System",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('accounts.urls')),  
    path('api/v1/elect/', include('elections.urls')),  
    path('api/v1/votes/', include('votes.urls')),  
    path('api/v1/blockchain/', include('blockchain.urls')), 

      # Rich Text Editor Uploads 
    path("ckeditor/", include("ckeditor_uploader.urls")),

    # API docs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
