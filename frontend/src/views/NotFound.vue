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
  background: #0f0f11;
}

.not-found__content {
  text-align: center;
}

.not-found__code {
  display: block;
  font-size: 6rem;
  font-weight: 800;
  color: #2a2a35;
  line-height: 1;
}

.not-found__title {
  font-size: 1.5rem;
  color: #e8e8f0;
  margin: 0.5rem 0;
}

.not-found__desc {
  color: #6666a0;
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
  transition: all 0.15s;
}

.btn--primary {
  background: #7c3aed;
  color: #fff;
}

.btn--primary:hover {
  background: #6d28d9;
}
</style>
