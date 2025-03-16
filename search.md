---
layout: default
title: search
permalink: /search/
---

<div style="view-transition-name: search-content">
  <h1>search</h1>
  
  <div class="search-container">
    <form action="/search/" method="get">
      <input type="text" id="search-box" name="query" placeholder="Search..." class="search-input">
      <button type="submit" class="search-button">Search</button>
    </form>
  </div>
  
  <div class="search-results">
    <!-- Results would be added here by a search engine like Jekyll Simple Search -->
    <p class="search-tip">Type in the box above to search for content</p>
  </div>
  
  <p><a href="javascript:history.back()" class="back-button">← Back</a></p>
</div>