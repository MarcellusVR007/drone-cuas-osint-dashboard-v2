<template>
  <div id="app">
    <header class="app-header">
      <div class="container">
        <h1>CUAS OSINT Dashboard V2</h1>
        <nav>
          <router-link to="/incidents">Incidents</router-link>
        </nav>
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
// No script logic needed yet
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f5f5;
  color: #333;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: #1a1a1a;
  color: white;
  padding: 1rem 0;
  border-bottom: 3px solid #e74c3c;
}

.app-header .container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.app-header nav a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.app-header nav a:hover {
  background: rgba(255, 255, 255, 0.1);
}

.app-main {
  flex: 1;
  padding: 2rem 0;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1rem;
}

/* Utility classes */
.card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 1.5rem;
}

.card h2 {
  font-size: 1.25rem;
  margin-bottom: 1rem;
  color: #1a1a1a;
  border-bottom: 2px solid #e74c3c;
  padding-bottom: 0.5rem;
}

.card h3 {
  font-size: 1rem;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  color: #555;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.btn-primary {
  background: #e74c3c;
  color: white;
}

.btn-primary:hover {
  background: #c0392b;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #888;
}

.error {
  background: #fee;
  border: 1px solid #fcc;
  padding: 1rem;
  border-radius: 4px;
  color: #c00;
  margin-bottom: 1rem;
}

table {
  width: 100%;
  border-collapse: collapse;
}

table th,
table td {
  text-align: left;
  padding: 0.75rem;
  border-bottom: 1px solid #eee;
}

table th {
  background: #f9f9f9;
  font-weight: 600;
  color: #555;
}

table tr:hover {
  background: #f9f9f9;
}

.field-row {
  display: flex;
  padding: 0.5rem 0;
  border-bottom: 1px solid #eee;
}

.field-row:last-child {
  border-bottom: none;
}

.field-label {
  font-weight: 600;
  color: #555;
  min-width: 180px;
}

.field-value {
  color: #333;
  flex: 1;
}

.confidence-bar {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 4px;
}

.confidence-bar-fill {
  height: 100%;
  background: linear-gradient(to right, #e74c3c, #27ae60);
  transition: width 0.3s;
}

.tag {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: #eee;
  border-radius: 4px;
  font-size: 0.85rem;
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
}

.tag-high {
  background: #d4edda;
  color: #155724;
}

.tag-medium {
  background: #fff3cd;
  color: #856404;
}

.tag-low {
  background: #f8d7da;
  color: #721c24;
}
</style>
