---
layout: default
title: HTML Posts
permalink: /category/html/
---

<div style="view-transition-name: filter-content">
  <h1>HTML Posts</h1>
  
  <div class="category-filters">
    <a href="/" class="filter-link">All Posts</a>
    <a href="/category/jekyll/" class="filter-link">Jekyll</a>
    <a href="/category/html/" class="filter-link active">HTML</a>
  </div>
  
  <ul class="post-list">
    {% for post in site.posts %}
      {% if post.categories contains "html" %}
        <li style="view-transition-name: post-{{ post.id | slugify }}">
          <span class="post-meta">{{ post.date | date: "%b %-d, %Y" }}</span>
          <h2>
            <a class="post-link" href="{{ post.url | relative_url }}">{{ post.title | escape }}</a>
          </h2>
          <p>{{ post.excerpt | strip_html | truncatewords: 30 }}</p>
        </li>
      {% endif %}
    {% endfor %}
  </ul>
</div>