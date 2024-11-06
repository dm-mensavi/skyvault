document.addEventListener('DOMContentLoaded', () => {
  const fileItems = document.querySelectorAll('.file-item');
  const contextMenu = document.querySelector('.context-menu');

  fileItems.forEach(item => {
    item.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      contextMenu.style.top = `${e.pageY}px`;
      contextMenu.style.left = `${e.pageX}px`;
      contextMenu.classList.add('active');
    });
  });

  document.addEventListener('click', () => {
    contextMenu.classList.remove('active');
  });
});
