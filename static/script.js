document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");

    uploadForm.addEventListener("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(uploadForm);

        fetch("/upload", {
            method: "POST",
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addImageToGallery(data.url, data.url.split('/').pop());
            } else {
                alert("Error uploading image.");
            }
        })
        .catch(error => console.error("Error:", error));
    });

    function addImageToGallery(imageUrl, filename) {
        const gallery = document.getElementById("gallery");
        const imageCard = document.createElement("div");
        imageCard.classList.add("image-card");
        imageCard.setAttribute("data-filename", filename);

        const img = document.createElement("img");
        img.src = imageUrl;
        img.alt = filename;

        const imageInfo = document.createElement("div");
        imageInfo.classList.add("image-info");

        const imageTitle = document.createElement("h3");
        imageTitle.classList.add("image-title");
        imageTitle.textContent = filename;

        const deleteButton = document.createElement("button");
        deleteButton.classList.add("delete-button");
        deleteButton.textContent = "Delete";

        const copyLinkButton = document.createElement("button");
        copyLinkButton.classList.add("copy-link-button");
        copyLinkButton.textContent = "Copy Link";
        copyLinkButton.setAttribute("data-url", imageUrl);

        imageInfo.appendChild(imageTitle);
        imageCard.appendChild(img);
        imageCard.appendChild(imageInfo);
        imageCard.appendChild(deleteButton);
        imageCard.appendChild(copyLinkButton);
        gallery.prepend(imageCard); // Add new images to the top of the gallery
    }

    document.getElementById("gallery").addEventListener("click", function (event) {
        if (event.target.classList.contains("delete-button")) {
            const imageCard = event.target.closest(".image-card");
            const filename = imageCard.getAttribute("data-filename");

            if (confirm(`Are you sure you want to delete '${filename}'?`)) {
                fetch(`/delete/${filename}`, {
                    method: "DELETE",
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        imageCard.remove();
                    } else {
                        alert("Error deleting image.");
                    }
                })
                .catch(error => console.error("Error:", error));
            }
        }

        if (event.target.classList.contains("copy-link-button")) {
            const url = event.target.getAttribute("data-url");
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(url).then(() => {
                    alert('Image link copied to clipboard!');
                }).catch(err => {
                    console.error('Error copying link: ', err);
                });
            } else {
                alert('Clipboard API not supported or not accessible.');
            }
        }
    });
});
