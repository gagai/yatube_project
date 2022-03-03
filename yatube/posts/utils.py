from django.core.paginator import Paginator


def get_page_obj(request, post_list, number):
    """Возвращает готовый паджинатор для постов."""
    paginator = Paginator(post_list, number)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return(page_obj)
