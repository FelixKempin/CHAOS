from django.urls import path
from . import views
from .views import InformationListView, InformationUpdateView, InformationDeleteView, toggle_status, \
    EmbeddingMapView, TagCreateAjaxView, TagAutocomplete, update_information_vault, search_neighbors


urlpatterns = [

    path('information/',InformationListView.as_view(),name='information_list'),
    path('information/<uuid:pk>/edit/', InformationUpdateView.as_view(), name='information_edit'),
    path('information/<uuid:pk>/delete/', InformationDeleteView.as_view(), name='information_delete'),
    path('information/<uuid:pk>/toggle-status/', toggle_status, name='information_toggle_status'),
    path(
        "information/embedding-map/",
        EmbeddingMapView.as_view(),
        name="information_map"
    ),
    path('ajax/tag/create/', TagCreateAjaxView.as_view(), name='tag-create-ajax'),
    path('tag-autocomplete/', TagAutocomplete.as_view(), name='tag-autocomplete'),
    path("information/<uuid:pk>/vaults/", update_information_vault, name="update_information_vault"),
    path(
        "information/embedding-map/search/",
        search_neighbors,
        name="information_map_search"
    ),
]