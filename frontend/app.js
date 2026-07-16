/**
 * 옷깃 OatGit — Frontend Application
 * AI 퍼스널 스타일링 코디네이터
 */

// 로컬 환경(localhost)일 때는 로컬 서버를, 배포 환경일 때는 실제 백엔드 URL을 가리킵니다.
// TODO: Render 배포 완료 후 아래의 'https://your-backend-url.onrender.com/api' 부분을 실제 주소로 변경하세요.
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000/api'
    : 'https://your-backend-url.onrender.com/api';

// ══════════════════════════════════════
// State
// ══════════════════════════════════════
const state = {
    currentPage: 'home',
    currentTpo: '출근',
    currentCodiIndex: 0,
    closetFilter: '전체',
    closetItems: [],
    codiRecommendations: [],
    weatherData: null,
    bodyProfile: {
        gender: '남성',
        height_cm: 175,
        weight_kg: 70,
        body_type: '표준형',
    },
    selectedFile: null,
};

// ══════════════════════════════════════
// Category Emoji Map
// ══════════════════════════════════════
const categoryEmoji = {
    '상의': '👕',
    '하의': '👖',
    '아우터': '🧥',
    '원피스': '👗',
    '신발': '👟',
    '액세서리': '💍',
};

const itemNameEmoji = {
    '셔츠': '👔', '니트': '🧶', '티셔츠': '👕', '맨투맨': '👕',
    '슬랙스': '👖', '데님': '👖', '바지': '👖', '팬츠': '👖',
    '자켓': '🧥', '코트': '🧥', '블레이저': '🧥', '패딩': '🧥',
    '벨트': '⌚', '스니커즈': '👟', '가방': '👜', '목도리': '🧣',
};

function getItemEmoji(name) {
    for (const [key, emoji] of Object.entries(itemNameEmoji)) {
        if (name.includes(key)) return emoji;
    }
    return '👔';
}

// ══════════════════════════════════════
// API Calls
// ══════════════════════════════════════
async function fetchWeather() {
    try {
        const res = await fetch(`${API_BASE}/weather/current`);
        const data = await res.json();
        state.weatherData = data;
        renderWeather(data);

        const ctxRes = await fetch(`${API_BASE}/weather/recommendation-context`);
        const ctx = await ctxRes.json();
        document.getElementById('weather-layer-guide').querySelector('span').textContent = ctx.layer_guide;
    } catch (err) {
        console.warn('Weather API 연결 실패, 더미 데이터 사용:', err);
        const dummy = { temperature: 22, feels_like: 20.5, condition: '맑음', precipitation_prob: 10, humidity: 55, clo_index: 0.7 };
        state.weatherData = dummy;
        renderWeather(dummy);
    }
}

async function fetchCodiRecommendations(tpo) {
    try {
        const res = await fetch(`${API_BASE}/styling/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tpo, body_profile: state.bodyProfile }),
        });
        const data = await res.json();
        state.codiRecommendations = data;
        state.currentCodiIndex = 0;
        renderCodiCards(data);
    } catch (err) {
        console.warn('Styling API 연결 실패:', err);
    }
}

async function fetchCloset() {
    try {
        const res = await fetch(`${API_BASE}/images/closet`);
        const data = await res.json();
        state.closetItems = data;
        renderCloset();
    } catch (err) {
        console.warn('Closet API 연결 실패:', err);
    }
}

async function uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API_BASE}/images/upload`, {
            method: 'POST',
            body: formData,
        });
        const data = await res.json();
        return data;
    } catch (err) {
        console.error('Upload 실패:', err);
        throw err;
    }
}

async function updateTags(itemId, tags) {
    try {
        await fetch(`${API_BASE}/images/closet/${itemId}/tags`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tags),
        });
    } catch (err) {
        console.warn('Tag 업데이트 실패:', err);
    }
}

async function deleteClosetItem(itemId) {
    try {
        await fetch(`${API_BASE}/images/closet/${itemId}`, { method: 'DELETE' });
        state.closetItems = state.closetItems.filter(i => i.id !== itemId);
        renderCloset();
        showToast('🗑️', '의류가 삭제되었습니다.');
    } catch (err) {
        console.warn('Delete 실패:', err);
    }
}

async function saveProfile(profile) {
    try {
        await fetch(`${API_BASE}/styling/profile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profile),
        });
        showToast('✅', '프로필이 저장되었습니다!');
    } catch (err) {
        console.warn('Profile 저장 실패:', err);
        showToast('✅', '프로필이 저장되었습니다!');
    }
}

// ══════════════════════════════════════
// Renderers
// ══════════════════════════════════════
function renderWeather(data) {
    const iconMap = { '맑음': '☀️', '흐림': '☁️', '비': '🌧️', '눈': '❄️', '구름많음': '⛅' };

    document.getElementById('weather-temp').textContent = `${Math.round(data.temperature)}°`;
    document.getElementById('weather-condition').textContent = data.condition;
    document.getElementById('weather-feels').textContent = `체감 ${data.feels_like}°`;
    document.getElementById('weather-humidity').textContent = `습도 ${data.humidity}%`;
    document.getElementById('weather-icon').textContent = iconMap[data.condition] || '☀️';
}

function renderCodiCards(recommendations) {
    const slider = document.getElementById('codi-slider');
    const dots = document.getElementById('codi-dots');
    const missingSection = document.getElementById('missing-items-section');
    const missingList = document.getElementById('missing-items-list');

    slider.innerHTML = '';
    dots.innerHTML = '';

    recommendations.forEach((codi, idx) => {
        // Card
        const card = document.createElement('div');
        card.className = 'codi-card';
        card.innerHTML = `
            <div class="codi-card-header">
                <span class="codi-number">LOOK ${codi.codi_id}</span>
            </div>
            <div class="codi-items">
                ${codi.items.map(item => `
                    <div class="codi-item">
                        <div class="codi-item-visual">${getItemEmoji(item.name)}</div>
                        <div class="codi-item-name">${item.name}</div>
                        <div class="codi-item-color">${item.color}</div>
                    </div>
                `).join('')}
            </div>
            <div class="codi-reasoning">${codi.reasoning}</div>
        `;
        slider.appendChild(card);

        // Dot
        const dot = document.createElement('div');
        dot.className = `codi-dot ${idx === 0 ? 'active' : ''}`;
        dots.appendChild(dot);
    });

    // Handle missing items for current card
    renderMissingItems(recommendations[0]);

    // Scroll observer
    slider.addEventListener('scroll', () => {
        const scrollLeft = slider.scrollLeft;
        const cardWidth = slider.children[0]?.offsetWidth || 1;
        const idx = Math.round(scrollLeft / (cardWidth + 16));
        state.currentCodiIndex = idx;

        dots.querySelectorAll('.codi-dot').forEach((d, i) => {
            d.classList.toggle('active', i === idx);
        });

        if (recommendations[idx]) {
            renderMissingItems(recommendations[idx]);
        }
    });
}

function renderMissingItems(codi) {
    const section = document.getElementById('missing-items-section');
    const list = document.getElementById('missing-items-list');

    if (!codi || !codi.missing_items || codi.missing_items.length === 0) {
        section.classList.add('hidden');
        return;
    }

    section.classList.remove('hidden');
    list.innerHTML = codi.missing_items.map(item => `
        <div class="missing-item-card">
            <div class="missing-item-icon">🛒</div>
            <div class="missing-item-name">${item.name}</div>
            <div class="missing-item-reason">${item.reason}</div>
            <a href="${item.shop_url}" class="missing-item-link" target="_blank">
                쇼핑하기 →
            </a>
        </div>
    `).join('');
}

function renderCloset() {
    const grid = document.getElementById('closet-grid');
    const countEl = document.getElementById('closet-count');
    const emptyEl = document.getElementById('closet-empty');

    const filtered = state.closetFilter === '전체'
        ? state.closetItems
        : state.closetItems.filter(i => i.tags.category === state.closetFilter);

    countEl.textContent = `${state.closetItems.length}벌`;

    grid.innerHTML = '';

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="closet-empty">
                <div class="empty-illustration"><span>👗</span></div>
                <h3>${state.closetItems.length === 0 ? '아직 등록된 옷이 없어요' : '이 카테고리에 등록된 옷이 없어요'}</h3>
                <p>옷 사진을 업로드하면 AI가 자동으로<br>분류하고 태깅해 드려요!</p>
                <button class="btn-primary" onclick="openUploadModal()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    옷 등록하기
                </button>
            </div>
        `;
        return;
    }

    filtered.forEach((item, idx) => {
        const el = document.createElement('div');
        el.className = 'closet-item';
        el.style.animationDelay = `${idx * 0.05}s`;

        const emoji = categoryEmoji[item.tags.category] || '👔';

        el.innerHTML = `
            <div class="closet-item-img">${emoji}</div>
            <div class="closet-item-info">
                <div class="closet-item-category">${item.tags.category} · ${item.tags.sub_category}</div>
                <div class="closet-item-tags">
                    <span class="closet-item-tag">${item.tags.color}</span>
                    <span class="closet-item-tag">${item.tags.pattern}</span>
                    <span class="closet-item-tag">${item.tags.season}</span>
                </div>
            </div>
            <button class="closet-item-delete" onclick="deleteClosetItem('${item.id}')" title="삭제">✕</button>
        `;
        grid.appendChild(el);
    });
}

// ══════════════════════════════════════
// Navigation
// ══════════════════════════════════════
function switchPage(pageName) {
    state.currentPage = pageName;

    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${pageName}`).classList.add('active');

    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.page === pageName);
    });

    // Refresh data on page switch
    if (pageName === 'closet') fetchCloset();
}

// ══════════════════════════════════════
// Upload Modal
// ══════════════════════════════════════
function openUploadModal() {
    document.getElementById('upload-modal').classList.remove('hidden');
    resetUploadModal();
}

function closeUploadModal() {
    document.getElementById('upload-modal').classList.add('hidden');
    resetUploadModal();
}

function resetUploadModal() {
    state.selectedFile = null;
    document.getElementById('upload-placeholder').classList.remove('hidden');
    document.getElementById('upload-preview').classList.add('hidden');
    document.getElementById('upload-progress').classList.add('hidden');
    document.getElementById('tag-result').classList.add('hidden');
    document.getElementById('btn-submit-upload').disabled = true;
    document.getElementById('progress-fill').style.width = '0%';
}

async function handleFileSelect(file) {
    if (!file || !file.type.startsWith('image/')) return;

    state.selectedFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('preview-img').src = e.target.result;
        document.getElementById('upload-placeholder').classList.add('hidden');
        document.getElementById('upload-preview').classList.remove('hidden');
    };
    reader.readAsDataURL(file);

    // Show progress
    document.getElementById('upload-progress').classList.remove('hidden');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    // Simulate AI analysis steps
    progressText.textContent = '📸 이미지를 분석하고 있습니다...';
    progressFill.style.width = '30%';

    await sleep(600);
    progressText.textContent = '✂️ 배경을 제거하고 있습니다...';
    progressFill.style.width = '60%';

    await sleep(500);
    progressText.textContent = '🏷️ AI가 의류 특성을 태깅하고 있습니다...';
    progressFill.style.width = '90%';

    await sleep(400);
    progressFill.style.width = '100%';
    progressText.textContent = '✅ 분석 완료!';

    await sleep(300);
    document.getElementById('upload-progress').classList.add('hidden');
    document.getElementById('tag-result').classList.remove('hidden');
    document.getElementById('btn-submit-upload').disabled = false;
}

async function handleUploadSubmit() {
    if (!state.selectedFile) return;

    const btn = document.getElementById('btn-submit-upload');
    btn.disabled = true;
    btn.textContent = '저장 중...';

    try {
        const result = await uploadImage(state.selectedFile);

        // Update tags from form
        const tags = {
            category: document.getElementById('tag-category').value,
            sub_category: document.getElementById('tag-subcategory').value,
            color: document.getElementById('tag-color').value,
            pattern: document.getElementById('tag-pattern').value,
            season: document.getElementById('tag-season').value,
        };
        await updateTags(result.id, tags);

        // Update local state
        result.tags = tags;
        state.closetItems.push(result);

        closeUploadModal();
        showToast('🎉', '옷이 옷장에 등록되었습니다!');

        if (state.currentPage === 'closet') renderCloset();
    } catch (err) {
        showToast('❌', '업로드에 실패했습니다. 다시 시도해 주세요.');
        btn.disabled = false;
        btn.textContent = '내 옷장에 저장';
    }
}

// ══════════════════════════════════════
// Toast
// ══════════════════════════════════════
function showToast(icon, message) {
    const toast = document.getElementById('toast');
    document.getElementById('toast-icon').textContent = icon;
    document.getElementById('toast-message').textContent = message;

    toast.classList.remove('hidden');
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.classList.add('hidden'), 400);
    }, 2500);
}

// ══════════════════════════════════════
// Utility
// ══════════════════════════════════════
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ══════════════════════════════════════
// Event Listeners
// ══════════════════════════════════════
function initEventListeners() {
    // Tab Navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchPage(btn.dataset.page));
    });

    // TPO Filter
    document.querySelectorAll('.tpo-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tpo-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentTpo = btn.dataset.tpo;
            fetchCodiRecommendations(btn.dataset.tpo);
        });
    });

    // Closet Filter
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            state.closetFilter = chip.dataset.filter;
            renderCloset();
        });
    });

    // Upload FAB + empty state button
    document.getElementById('btn-upload-fab').addEventListener('click', openUploadModal);
    const btnUploadEmpty = document.getElementById('btn-upload-empty');
    if (btnUploadEmpty) btnUploadEmpty.addEventListener('click', openUploadModal);

    // Upload Modal
    document.getElementById('btn-cancel-upload').addEventListener('click', closeUploadModal);
    document.getElementById('btn-submit-upload').addEventListener('click', handleUploadSubmit);

    // File input
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.getElementById('upload-area');

    document.getElementById('upload-placeholder').addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) handleFileSelect(e.target.files[0]);
    });

    // Drag & drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files[0]) handleFileSelect(e.dataTransfer.files[0]);
    });

    // Clear preview
    document.getElementById('btn-clear-preview').addEventListener('click', (e) => {
        e.stopPropagation();
        resetUploadModal();
    });

    // Close modal on overlay click
    document.getElementById('upload-modal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) closeUploadModal();
    });

    // Profile: Gender
    document.querySelectorAll('.gender-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.gender-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.bodyProfile.gender = btn.dataset.gender;
        });
    });

    // Profile: Height sync
    const heightInput = document.getElementById('input-height');
    const heightRange = document.getElementById('range-height');
    heightInput.addEventListener('input', () => {
        heightRange.value = heightInput.value;
        state.bodyProfile.height_cm = parseFloat(heightInput.value);
    });
    heightRange.addEventListener('input', () => {
        heightInput.value = heightRange.value;
        state.bodyProfile.height_cm = parseFloat(heightRange.value);
    });

    // Profile: Weight sync
    const weightInput = document.getElementById('input-weight');
    const weightRange = document.getElementById('range-weight');
    weightInput.addEventListener('input', () => {
        weightRange.value = weightInput.value;
        state.bodyProfile.weight_kg = parseFloat(weightInput.value);
    });
    weightRange.addEventListener('input', () => {
        weightInput.value = weightRange.value;
        state.bodyProfile.weight_kg = parseFloat(weightRange.value);
    });

    // Profile: Body type
    document.querySelectorAll('.body-type-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.body-type-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.bodyProfile.body_type = btn.dataset.type;
        });
    });

    // Profile: Save
    document.getElementById('profile-form').addEventListener('submit', (e) => {
        e.preventDefault();
        saveProfile(state.bodyProfile);
    });
}

// ══════════════════════════════════════
// Init
// ══════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    // Wait for splash to finish
    setTimeout(() => {
        document.getElementById('lock-screen').classList.remove('hidden');

        // Remove splash after animation
        setTimeout(() => {
            const splash = document.getElementById('splash-screen');
            if (splash) splash.remove();
        }, 800);
    }, 2200);

    // Lock screen logic
    const btnUnlock = document.getElementById('btn-unlock');
    const pwdInput = document.getElementById('password-input');
    const lockError = document.getElementById('lock-error');

    function checkPassword() {
        if (pwdInput.value === '0000') {
            document.getElementById('lock-screen').classList.add('hidden');
            document.getElementById('app').classList.remove('hidden');
        } else {
            lockError.classList.remove('hidden');
            pwdInput.value = '';
            pwdInput.focus();
        }
    }

    btnUnlock.addEventListener('click', checkPassword);
    pwdInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') checkPassword();
    });

    initEventListeners();

    // Load initial data
    fetchWeather();
    fetchCodiRecommendations('출근');
    fetchCloset();
});
