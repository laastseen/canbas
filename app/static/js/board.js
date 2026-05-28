document.addEventListener('DOMContentLoaded', () => {
  const tasks = document.querySelectorAll('.kanban-task');
  const columns = document.querySelectorAll('.kanban-column');
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

  tasks.forEach((task) => {
    task.addEventListener('dragstart', (event) => {
      task.classList.add('dragging');
      event.dataTransfer.setData('text/plain', task.dataset.taskId);
      event.dataTransfer.effectAllowed = 'move';
    });

    task.addEventListener('dragend', () => {
      task.classList.remove('dragging');
    });
  });

  columns.forEach((column) => {
    column.addEventListener('dragover', (event) => {
      event.preventDefault();
      event.dataTransfer.dropEffect = 'move';
    });

    column.addEventListener('drop', async (event) => {
      event.preventDefault();
      const taskId = event.dataTransfer.getData('text/plain');
      const task = document.querySelector(`.kanban-task[data-task-id="${taskId}"]`);
      if (!task) {
        return;
      }

      const status = column.dataset.status;
      const response = await fetch(`/tasks/${taskId}/board-update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ status })
      });

      if (!response.ok) {
        window.location.reload();
        return;
      }

      const emptyState = column.querySelector('.empty-column');
      if (emptyState) {
        emptyState.remove();
      }
      column.appendChild(task);
    });
  });
});
