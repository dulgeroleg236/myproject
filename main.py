
from django.db import models
from django.urls import reverse, NoReverseMatch

class Menu(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    title = models.CharField(max_length=100)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='items')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    url = models.CharField(max_length=200, blank=True)
    named_url = models.CharField(max_length=200, blank=True)

    def get_absolute_url(self):
        if self.named_url:
            try:
                return reverse(self.named_url)
            except NoReverseMatch:
                return '#'
        return self.url or '#'

    def __str__(self):
        return self.title



from django import template
from django.urls import resolve
from ..models import Menu, MenuItem
from django.utils.safestring import mark_safe
from collections import defaultdict

register = template.Library()

@register.inclusion_tag('menu/draw_menu.html', takes_context=True)
def draw_menu(context, menu_name):
    request = context['request']
    current_url = request.path
    menu = Menu.objects.prefetch_related('items__children').get(name=menu_name)
    items = list(menu.items.all())

    tree = defaultdict(list)
    items_by_id = {}

    for item in items:
        items_by_id[item.id] = item
        tree[item.parent_id].append(item)

    def build_tree(parent_id=None):
        nodes = []
        for item in tree[parent_id]:
            item_url = item.get_absolute_url()
            children = build_tree(item.id)
            is_active = current_url.startswith(item_url)
            nodes.append({
                'item': item,
                'children': children,
                'is_active': is_active,
                'show_children': is_active or any(c['is_active'] for c in children),
            })
        return nodes

    return {'menu_tree': build_tree(), 'request': request}



<ul>
    {% for node in menu_tree %}
        {% include "menu/menu_node.html" with node=node %}
    {% endfor %}
</ul>



<li>
    <a href="{{ node.item.get_absolute_url }}" class="{% if node.is_active %}active{% endif %}">{{ node.item.title }}</a>
    {% if node.children and node.show_children %}
        <ul>
            {% for child in node.children %}
                {% include "menu/menu_node.html" with node=child %}
            {% endfor %}
        </ul>
    {% endif %}
</li>


### admin.py
from django.contrib import admin
from .models import Menu, MenuItem

class MenuItemInline(admin.StackedInline):
    model = MenuItem
    extra = 1

class MenuAdmin(admin.ModelAdmin):
    inlines = [MenuItemInline]

admin.site.register(Menu, MenuAdmin)


### usage in template
{% load menu_tags %}
{% draw_menu 'main_menu' %}


### apps.py
from django.apps import AppConfig

class TreeMenuConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tree_menu'


### __init__.py
# (empty)


### __init__.py in templatetags directory
# (empty)


### migrations/__init__.py
# (empty)


### settings.py (add 'tree_menu' to INSTALLED_APPS)
# 'tree_menu',


