# bakla_io_project/settings.py

from pathlib import Path

# Projenin kök dizini (manage.py'nin olduğu yer)
BASE_DIR = Path(__file__).resolve().parent.parent

# GÜVENLİK UYARISI: Canlı ortamda bu anahtarı değiştir ve gizli tut!
SECRET_KEY = 'django-insecure-bu-anahtar-sadece-test-icindir'

# Geliştirme sırasında DEBUG modunu açık tut.
DEBUG = True

ALLOWED_HOSTS = []


# --- Uygulama Tanımları ---
INSTALLED_APPS = [
    # Yerel Uygulamalar (Bizim oluşturduklarımız)
    'users.apps.UsersConfig',
    'posts.apps.PostsConfig',
    'economy.apps.EconomyConfig',
    'notifications.apps.NotificationsConfig',
    'django_htmx',

    # Üçüncü Parti Uygulamalar (Bizim kurduklarımız)
    'tailwind',
    'theme',

    # Django'nun Standart Uygulamaları
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Özel kullanıcı modelimizi tanıtıyoruz
AUTH_USER_MODEL = 'users.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bakla_io_project.urls'


# --- Şablon (Template) Ayarları ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Proje genelindeki 'templates' klasörünü Django'ya tanıtıyoruz
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # YENİ SATIR:
                'notifications.context_processors.unread_notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'bakla_io_project.wsgi.application'


# --- Veritabanı Ayarları ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --- Şifre Doğrulama Ayarları ---
AUTH_PASSWORD_VALIDATORS = []


# --- Uluslararasılaştırma Ayarları ---
LANGUAGE_CODE = 'tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True


# --- Statik Dosya Ayarları ---
STATIC_URL = 'static/'


# --- Varsayılan Birincil Anahtar Ayarı ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Tailwind CSS Ayarları ---
# django-tailwind paketine, dosyalarını yöneteceği uygulamanın adını söylüyoruz
TAILWIND_APP_NAME = 'theme'

# Django'nun Tailwind'i tetikleyebilmesi için dahili IP ayarı (Geliştirme için)
INTERNAL_IPS = [
    "127.0.0.1",
]
# settings.py dosyasının en altına ekle

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'