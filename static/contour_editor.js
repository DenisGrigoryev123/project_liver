class ContourEditor {
    constructor() {
        this.initElements();
        this.initState();
        this.initCanvas();
        this.setupEventListeners();
        this.loadImages();
    }

    initElements() {
        this.originalCanvas = document.getElementById('original-ct');
        this.contourCanvas = document.getElementById('contour-canvas');
        this.drawBtn = document.getElementById('draw-btn');
        this.eraseBtn = document.getElementById('erase-btn');
        this.clearBtn = document.getElementById('clear-btn');
        this.saveBtn = document.getElementById('save-btn');
        this.brushSize = document.getElementById('brush-size');
    }

    initState() {
        this.isDrawing = false;
        this.mode = 'draw';
        this.currentColor = '#FF0000';
        this.lastX = 0;
        this.lastY = 0;

        // Инициализация контекстов
        this.originalCtx = this.originalCanvas.getContext('2d');
        this.ctx = this.contourCanvas.getContext('2d');

        // Настройка контура
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        this.ctx.strokeStyle = this.currentColor;
        this.ctx.lineWidth = this.brushSize.value;
    }

    initCanvas() {
        // Очистка и настройка canvas
        this.originalCtx.clearRect(0, 0, this.originalCanvas.width, this.originalCanvas.height);
        this.ctx.clearRect(0, 0, this.contourCanvas.width, this.contourCanvas.height);

        // Установка фона для оригинального изображения
        this.originalCtx.fillStyle = '#000000';
        this.originalCtx.fillRect(0, 0, this.originalCanvas.width, this.originalCanvas.height);
    }

    setupEventListeners() {
        // Обработчики мыши
        this.contourCanvas.addEventListener('mousedown', this.startDrawing.bind(this));
        this.contourCanvas.addEventListener('mousemove', this.draw.bind(this));
        this.contourCanvas.addEventListener('mouseup', this.stopDrawing.bind(this));
        this.contourCanvas.addEventListener('mouseout', this.stopDrawing.bind(this));

        // Кнопки инструментов
        this.drawBtn.addEventListener('click', () => this.setMode('draw'));
        this.eraseBtn.addEventListener('click', () => this.setMode('erase'));
        this.clearBtn.addEventListener('click', this.resetCanvas.bind(this));
        this.saveBtn.addEventListener('click', this.saveContour.bind(this));

        // Горячие клавиши
        document.addEventListener('keydown', (e) => {
            if (e.key.toLowerCase() === 'd') this.setMode('draw');
            if (e.key.toLowerCase() === 'e') this.setMode('erase');
            if (e.key.toLowerCase() === 'c') this.resetCanvas();
            if (e.key.toLowerCase() === 's') this.saveContour();
        });

        // Изменение размера кисти
        this.brushSize.addEventListener('input', () => {
            this.ctx.lineWidth = this.brushSize.value;
        });
    }

    setMode(mode) {
        this.mode = mode;
        this.drawBtn.classList.toggle('active', mode === 'draw');
        this.eraseBtn.classList.toggle('active', mode === 'erase');
        this.contourCanvas.style.cursor = mode === 'draw' ? 'crosshair' : 'cell';
    }

    startDrawing(e) {
        this.isDrawing = true;
        [this.lastX, this.lastY] = this.getMousePos(e);
        this.ctx.beginPath();
        this.ctx.moveTo(this.lastX, this.lastY);
    }

    draw(e) {
        if (!this.isDrawing) return;

        const [x, y] = this.getMousePos(e);

        this.ctx.globalCompositeOperation = this.mode === 'draw' ? 'source-over' : 'destination-out';

        this.ctx.lineTo(x, y);
        this.ctx.stroke();
        this.ctx.beginPath();
        this.ctx.moveTo(x, y);

        [this.lastX, this.lastY] = [x, y];
    }

    stopDrawing() {
        this.isDrawing = false;
    }

    getMousePos(e) {
        const rect = this.contourCanvas.getBoundingClientRect();
        return [
            e.clientX - rect.left,
            e.clientY - rect.top
        ];
    }

    resetCanvas() {
        if (confirm('Вы уверены, что хотите сбросить все изменения?')) {
            this.ctx.clearRect(0, 0, this.contourCanvas.width, this.contourCanvas.height);
            this.loadContourImage();
        }
    }

    async saveContour() {
        try {
            const combinedCanvas = document.createElement('canvas');
            combinedCanvas.width = this.originalCanvas.width;
            combinedCanvas.height = this.originalCanvas.height;
            const combinedCtx = combinedCanvas.getContext('2d');

            combinedCtx.drawImage(this.originalCanvas, 0, 0);
            combinedCtx.drawImage(this.contourCanvas, 0, 0);

            const link = document.createElement('a');
            link.download = 'liver_contour.png';
            link.href = combinedCanvas.toDataURL('image/png');
            link.click();

        } catch (error) {
            console.error('Ошибка сохранения:', error);
            alert('Не удалось сохранить изображение');
        }
    }

    loadImages() {
        this.loadOriginalImage();
        this.loadContourImage();
    }

    loadOriginalImage() {
        const img = new Image();
        img.crossOrigin = 'Anonymous';
        img.onload = () => {
            this.originalCtx.drawImage(img, 0, 0, this.originalCanvas.width, this.originalCanvas.height);
            console.log('Основное изображение загружено');
        };
        img.onerror = (e) => {
            console.error('Ошибка загрузки основного изображения:', e);
        };
        img.src = '/original_image?t=' + Date.now(); // Добавляем timestamp для избежания кеширования
    }

    loadContourImage() {
        const img = new Image();
        img.crossOrigin = 'Anonymous';
        img.onload = () => {
            this.ctx.drawImage(img, 0, 0, this.contourCanvas.width, this.contourCanvas.height);
            console.log('Контурное изображение загружено');
        };
        img.onerror = (e) => {
            console.error('Ошибка загрузки контурного изображения:', e);
        };
        img.src = '/contour_image?t=' + Date.now();
    }
}

// Инициализация редактора
document.addEventListener('DOMContentLoaded', () => {
    new ContourEditor();
});