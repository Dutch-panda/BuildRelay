// Essential reading and native navigation remain available without JavaScript.
const menu = document.querySelector('.sidebar details');
const narrow = window.matchMedia('(max-width: 760px)');
function adaptNavigation() {
  if (menu) menu.open = !narrow.matches || menu.contains(document.activeElement);
}
adaptNavigation();
narrow.addEventListener('change', adaptNavigation);

document.querySelectorAll('pre > code').forEach((code, index) => {
  const controls = document.createElement('div');
  controls.className = 'code-controls';
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = 'Copy code';
  button.setAttribute('aria-label', `Copy code block ${index + 1}`);
  const status = document.createElement('span');
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  button.addEventListener('click', async () => {
    status.textContent = '';
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(code.textContent);
      status.textContent = 'Copied.';
    } catch {
      status.textContent = 'Could not copy. Select the code and copy it manually.';
    }
  });
  controls.append(button, status);
  code.parentElement.before(controls);
});
