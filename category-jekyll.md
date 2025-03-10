---
layout: default
title: Jekyll Posts
permalink: /category/jekyll/
---

<div style="view-transition-name: filter-content">
  <h1>Jekyll Posts</h1>
  
  <div class="category-filters">
    <a href="/" class="filter-link">All Posts</a>
    <a href="/category/jekyll/" class="filter-link active">Jekyll</a>
    <a href="/category/html/" class="filter-link">HTML</a>
  </div>
  
  <ul class="post-list">
    {% for post in site.posts %}
      {% if post.categories contains "jekyll" %}
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