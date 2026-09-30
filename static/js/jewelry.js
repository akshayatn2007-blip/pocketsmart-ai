/**
 * PocketSmart AI - Jewelry Planner Client Script
 */

document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('outfit_image');
  const previewBox = document.getElementById('image-preview');
  const previewImg = document.getElementById('preview-img');
  const fileNameDisplay = document.getElementById('file-name');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('active');
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('active');
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('active');
      if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFile(fileInput.files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length) {
        handleFile(fileInput.files[0]);
      }
    });
  }

  function handleFile(file) {
    if (!file) return;

    // Check size limit: 5MB
    if (file.size > 5 * 1024 * 1024) {
      alert("File is too large! Maximum image size is 5MB.");
      fileInput.value = "";
      return;
    }

    if (fileNameDisplay) {
      fileNameDisplay.textContent = file.name;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      if (previewImg && previewBox) {
        previewImg.src = e.target.result;
        previewBox.style.display = 'block';
      }
    };
    reader.readAsDataURL(file);
  }
});
