<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  onMount(() => {
    goto('/settings?tab=templates');
  });
</script>

<div class="redirect">
  <p>Redirecting to Settings...</p>
</div>

<style>
  .redirect {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 50vh;
    color: var(--color-text-secondary);
  }
</style>
