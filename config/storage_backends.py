# config/storage_backends.py

import os
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class SupabaseS3Storage(S3Boto3Storage):
    """
    Custom storage backend for Supabase S3-compatible storage.
    Fixes URL generation for public bucket access.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_ref = getattr(settings, 'SUPABASE_PROJECT_REF', '')
    
    def url(self, name):
        """
        Generate correct public URL for Supabase storage.
        Format: https://{project_ref}.supabase.co/storage/v1/object/public/{bucket}/{path}
        """
        if not name:
            return ''
        
        # Clean the name (remove leading slashes)
        name = str(name).lstrip('/')
        
        # Return the public URL format for Supabase
        return f"https://{self.project_ref}.supabase.co/storage/v1/object/public/{self.bucket_name}/{name}"
    

class PrivateSupabaseStorage(S3Boto3Storage):
    """
    Private storage for medical documents.
    Generates signed URLs that expire.
    """
    bucket_name = 'medical-records'
    default_acl = 'private'
    file_overwrite = False
    querystring_auth = True  # Forces signed URLs
    querystring_expire = 3600  # URLs expire in 1 hour
    custom_domain = None  # Disable custom domain to use signed URL generation
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_ref = getattr(settings, 'SUPABASE_PROJECT_REF', '')
        self.access_key = os.getenv('SUPABASE_ACCESS_KEY_ID')
        self.secret_key = os.getenv('SUPABASE_SECRET_ACCESS_KEY')
        self.endpoint_url = os.getenv('SUPABASE_S3_ENDPOINT_URL')
        self.region_name = os.getenv('SUPABASE_REGION', 'eu-west-2')    