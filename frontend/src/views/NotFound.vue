<template>
  <div class="not-found">
    <div class="not-found__content">
      <span class="not-found__code">404</span>
      <h1 class="not-found__title">Page not found</h1>
      <p class="not-found__desc">The page you're looking for doesn't exist.</p>
      <RouterLink to="/" class="btn btn--primary">Go to Dashboard</RouterLink>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg-app, #09090b);
}

.not-found__content {
  text-align: center;
}

.not-found__code {
  display: block;
  font-size: 6rem;
  font-weight: 800;
  color: var(--border-strong, #323242);
  line-height: 1;
}

.not-found__title {
  font-size: 1.5rem;
  color: var(--text-main, #f4f4f7);
  margin: 0.5rem 0;
}

.not-found__desc {
  color: var(--text-muted, #9494a8);
  margin-bottom: 1.5rem;
}

.btn {
  display: inline-block;
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  text-decoration: none;
  transition: all var(--transition-fast, 0.15s ease);
}

.btn--primary {
  background: var(--primary, #7c3aed);
  color: #fff;
}

.btn--primary:hover {
  background: var(--primary-hover, #6d28d9);
}
</style>
