/**
 * EduQuestion AI - Frontend Application Logic
 */

// State Management
const state = {
    currentTab: 'text', // 'text' | 'pdf'
    viewMode: 'study',  // 'study' | 'quiz'
    generatedData: null,
    userAnswers: {},
    quizSubmitted: false,
    selectedPdfFile: null
};

// Educational Presets
const PRESETS = {
    photosynthesis: `Photosynthesis is the process by which green plants, algae, and certain bacteria convert sunlight, water, and carbon dioxide into chemical energy stored in glucose molecules. During this biological reaction, chlorophyll in plant chloroplasts captures solar photons, initiating reactions between absorbed water (H2O) and atmospheric carbon dioxide (CO2). As a vital byproduct, oxygen gas (O2) is released into the atmosphere, sustaining aerobic organisms across Earth. Photosynthesis consists of two stages: light-dependent reactions which synthesize ATP and NADPH in the thylakoid membranes, and the Calvin cycle (light-independent reactions) in the stroma which fixes carbon dioxide into carbohydrates.`,
    ai: `Artificial Intelligence (AI) refers to the computational simulation of human intelligence processes by computer systems. Machine learning (ML) is a core subset of AI that provides systems the capability to automatically learn and improve from experience without being explicitly programmed. Deep learning, a specialized branch of machine learning, employs multi-layered artificial neural networks inspired by biological neural circuits in the human brain. Supervised learning utilizes labeled datasets to train models for classification and regression, whereas unsupervised learning identifies latent clusters and patterns within unlabeled data.`,
    physics: `Newton's laws of motion comprise three fundamental physical principles that form the basis of classical mechanics. The First Law (Law of Inertia) asserts that an object remains at rest or in uniform straight-line motion unless acted upon by an external net force. The Second Law establishes that the acceleration of an object is directly proportional to the net force acting upon it and inversely proportional to its mass, mathematically formulated as F = ma. The Third Law states that for every action, there is an equal and opposite reaction, meaning forces always occur in matched interaction pairs between two bodies.`
};

// Initialization on DOM Load
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    checkApiHealth();
    setupDropzone();
    setupTextareaCounter();
    loadPreset('photosynthesis');
});

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('edu_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    const toggleBtn = document.getElementById('theme-toggle-btn');
    toggleBtn.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('edu_theme', next);
    });
}

// Health Check
async function checkApiHealth() {
    const statusEl = document.getElementById('api-status');
    try {
        const res = await fetch('/health');
        if (res.ok) {
            statusEl.className = 'status-indicator online';
            statusEl.querySelector('.status-label').textContent = 'API Connected';
        } else {
            throw new Error('API non-200 response');
        }
    } catch {
        statusEl.className = 'status-indicator offline';
        statusEl.querySelector('.status-label').textContent = 'API Offline';
    }
}

// Tab Switching
function setTab(tab) {
    state.currentTab = tab;
    document.getElementById('tab-btn-text').classList.toggle('active', tab === 'text');
    document.getElementById('tab-btn-pdf').classList.toggle('active', tab === 'pdf');
    document.getElementById('content-text').classList.toggle('active', tab === 'text');
    document.getElementById('content-pdf').classList.toggle('active', tab === 'pdf');
    hideError();
}

// Textarea & Presets
function setupTextareaCounter() {
    const textarea = document.getElementById('material-text');
    const counter = document.getElementById('char-count');
    textarea.addEventListener('input', () => {
        counter.textContent = `${textarea.value.length} characters`;
    });
}

function loadPreset(key) {
    const textarea = document.getElementById('material-text');
    textarea.value = PRESETS[key] || '';
    document.getElementById('char-count').textContent = `${textarea.value.length} characters`;
    hideError();
}

function clearText() {
    const textarea = document.getElementById('material-text');
    textarea.value = '';
    document.getElementById('char-count').textContent = '0 characters';
}

// PDF Drag & Drop Setup
function setupDropzone() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('pdf-file-input');

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handlePdfFileSelection(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handlePdfFileSelection(e.target.files[0]);
        }
    });
}

function handlePdfFileSelection(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showError('Only PDF files are supported.');
        return;
    }
    if (file.size > 5 * 1024 * 1024) {
        showError('File exceeds the 5MB maximum size limit.');
        return;
    }

    state.selectedPdfFile = file;
    const badge = document.getElementById('file-info-badge');
    const nameEl = document.getElementById('file-name-text');
    const sizeKb = Math.round(file.size / 1024);
    nameEl.textContent = `${file.name} (${sizeKb} KB)`;
    badge.style.display = 'inline-flex';
    hideError();
}

function removeSelectedFile(event) {
    event.stopPropagation();
    state.selectedPdfFile = null;
    document.getElementById('pdf-file-input').value = '';
    document.getElementById('file-info-badge').style.display = 'none';
}

// Stepper & Slider
function updateCountDisplay(val) {
    document.getElementById('count-display').textContent = val;
}

function stepCount(delta) {
    const slider = document.getElementById('question-count');
    let val = parseInt(slider.value) + delta;
    if (val < 1) val = 1;
    if (val > 50) val = 50;
    slider.value = val;
    updateCountDisplay(val);
}

// Generate Questions Handler
async function handleGenerate() {
    hideError();
    const btn = document.getElementById('generate-btn');
    const spinner = document.getElementById('btn-spinner');
    const btnText = document.getElementById('btn-text');

    const count = parseInt(document.getElementById('question-count').value);
    const qType = document.getElementById('question-type').value;
    const diff = document.getElementById('difficulty-level').value;
    const cognitive = document.getElementById('cognitive-level').value || null;

    btn.disabled = true;
    spinner.style.display = 'block';
    btnText.textContent = 'Generating with AI...';

    try {
        let responseData;

        if (state.currentTab === 'text') {
            const textContent = document.getElementById('material-text').value.trim();
            if (!textContent) {
                throw new Error('Educational material cannot be empty.');
            }
            if (textContent.length < 10) {
                throw new Error('Please provide at least 10 characters of educational text.');
            }

            let endpoint = '/api/v1/questions/generate';
            let payload = {
                text: textContent,
                number_of_questions: count,
                question_type: qType,
                difficulty: diff,
                cognitive_level: cognitive
            };

            if (qType === 'mixed') {
                endpoint = '/api/v1/questions/mixed';
                payload = {
                    text: textContent,
                    number_of_questions: count,
                    difficulty: diff,
                    cognitive_level: cognitive
                };
            }

            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            responseData = await res.json();
            if (!res.ok) {
                throw new Error(responseData.detail || 'Failed to generate questions');
            }

        } else {
            // PDF mode
            if (!state.selectedPdfFile) {
                throw new Error('Please select or drop a PDF file to upload.');
            }

            const formData = new FormData();
            formData.append('file', state.selectedPdfFile);
            formData.append('number_of_questions', count);
            formData.append('question_type', qType);
            formData.append('difficulty', diff);
            if (cognitive) {
                formData.append('cognitive_level', cognitive);
            }

            const res = await fetch('/api/v1/questions/generate-from-pdf', {
                method: 'POST',
                body: formData
            });

            responseData = await res.json();
            if (!res.ok) {
                throw new Error(responseData.detail || 'Failed to extract text from PDF');
            }
        }

        state.generatedData = responseData;
        state.userAnswers = {};
        state.quizSubmitted = false;
        renderResults();
        showToast(`Successfully generated ${responseData.total_questions} questions!`);

    } catch (err) {
        showError(err.message);
    } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
        btnText.textContent = 'Generate Assessment Questions';
    }
}

// Render Results in Study or Quiz Mode
function renderResults() {
    const container = document.getElementById('results-area');
    const list = document.getElementById('questions-container');
    const data = state.generatedData;

    if (!data || !data.questions) return;

    // Update Metadata
    document.getElementById('meta-total').textContent = `${data.total_questions} Questions`;
    document.getElementById('meta-source').textContent = `Source: ${data.source_type.toUpperCase()}`;
    const provider = data.metadata?.ai_provider || 'Generative AI';
    document.getElementById('meta-provider').textContent = `Engine: ${provider}`;

    // Reset Quiz state if not submitted
    if (!state.quizSubmitted) {
        document.getElementById('quiz-score-card').style.display = 'none';
    }

    const isQuiz = (state.viewMode === 'quiz');
    document.getElementById('quiz-submit-bar').style.display = isQuiz && !state.quizSubmitted ? 'block' : 'none';

    list.innerHTML = '';

    data.questions.forEach((q, index) => {
        const card = document.createElement('div');
        card.className = 'question-card';
        card.id = `q-card-${index}`;

        const diffClass = `badge-${q.difficulty || 'medium'}`;
        const bloomBadge = q.cognitive_level ? `<span class="badge badge-bloom">${q.cognitive_level}</span>` : '';

        let optionsMarkup = '';

        if (q.options && q.options.length > 0) {
            optionsMarkup = '<div class="options-grid">';
            q.options.forEach((opt, optIdx) => {
                const optLetter = String.fromCharCode(65 + optIdx);
                let choiceClass = 'option-choice';
                const isUserSelected = state.userAnswers[index] === opt;

                if (isQuiz) {
                    choiceClass += ' quiz-interactive';
                    if (isUserSelected) choiceClass += ' selected';

                    if (state.quizSubmitted) {
                        if (opt === q.answer) {
                            choiceClass += ' user-correct';
                        } else if (isUserSelected && opt !== q.answer) {
                            choiceClass += ' user-wrong';
                        }
                    }

                    optionsMarkup += `
                        <div class="${choiceClass}" onclick="selectQuizOption(${index}, '${escapeAttr(opt)}')">
                            <span class="opt-prefix">${optLetter}</span>
                            <span style="flex:1;">${opt}</span>
                            <input type="radio" name="q-${index}" class="opt-radio" ${isUserSelected ? 'checked' : ''} ${state.quizSubmitted ? 'disabled' : ''}>
                        </div>
                    `;
                } else {
                    // Study Mode
                    const isCorrect = (opt === q.answer);
                    if (isCorrect) choiceClass += ' study-correct';

                    optionsMarkup += `
                        <div class="${choiceClass}">
                            <span class="opt-prefix">${optLetter}</span>
                            <span style="flex: 1;">${opt}</span>
                            ${isCorrect ? '<span style="font-weight:700; font-size:0.85rem;">✓ Correct Answer</span>' : ''}
                        </div>
                    `;
                }
            });
            optionsMarkup += '</div>';
        } else {
            // Short Answer
            if (isQuiz) {
                const userText = state.userAnswers[index] || '';
                optionsMarkup = `
                    <div>
                        <input type="text" class="short-ans-input" placeholder="Type your answer here..." 
                            value="${escapeAttr(userText)}" 
                            oninput="saveShortAnswer(${index}, this.value)"
                            ${state.quizSubmitted ? 'disabled' : ''}>
                        ${state.quizSubmitted ? `<div class="option-choice study-correct" style="margin-bottom:1rem;"><strong>Model Answer:</strong> ${q.answer}</div>` : ''}
                    </div>
                `;
            } else {
                optionsMarkup = `
                    <div class="option-choice study-correct" style="margin-bottom: 1rem;">
                        <strong>Answer:</strong> ${q.answer}
                    </div>
                `;
            }
        }

        // Explanation (always visible in study mode, visible in quiz mode only after submission)
        let explanationMarkup = '';
        if (!isQuiz || state.quizSubmitted) {
            explanationMarkup = `
                <div class="explanation-box">
                    <strong>Explanation:</strong> ${q.explanation || 'Derived from the educational study material.'}
                </div>
            `;
        }

        card.innerHTML = `
            <div class="q-header">
                <div class="badge-group">
                    <span class="badge ${diffClass}">${q.difficulty}</span>
                    <span class="badge badge-type">${q.type.replace('_', ' ')}</span>
                    ${bloomBadge}
                </div>
                <span style="font-size:0.85rem; font-weight:700; color:var(--text-muted);">Q${q.id || (index + 1)}</span>
            </div>
            <div class="q-text">${q.question}</div>
            ${optionsMarkup}
            ${explanationMarkup}
        `;

        list.appendChild(card);
    });

    container.style.display = 'block';
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Mode Switcher (Study vs Quiz)
function switchViewMode(mode) {
    state.viewMode = mode;
    document.getElementById('mode-study-btn').classList.toggle('active', mode === 'study');
    document.getElementById('mode-quiz-btn').classList.toggle('active', mode === 'quiz');
    renderResults();
}

// Quiz Interaction
function selectQuizOption(qIdx, optionValue) {
    if (state.quizSubmitted) return;
    state.userAnswers[qIdx] = optionValue;
    renderResults();
}

function saveShortAnswer(qIdx, val) {
    state.userAnswers[qIdx] = val;
}

function submitQuiz() {
    state.quizSubmitted = true;
    const questions = state.generatedData.questions;
    let correctCount = 0;

    questions.forEach((q, idx) => {
        const userAns = (state.userAnswers[idx] || '').trim().toLowerCase();
        const correctAns = (q.answer || '').trim().toLowerCase();
        if (userAns && (userAns === correctAns || (q.type === 'short_answer' && userAns.includes(correctAns)))) {
            correctCount++;
        }
    });

    const percent = Math.round((correctCount / questions.length) * 100);
    const scoreCard = document.getElementById('quiz-score-card');
    document.getElementById('score-percentage').textContent = `${percent}%`;
    document.getElementById('score-message').textContent = `You answered ${correctCount} out of ${questions.length} questions correctly.`;

    if (percent >= 80) {
        document.getElementById('score-title').textContent = '🎉 Outstanding Performance!';
    } else if (percent >= 50) {
        document.getElementById('score-title').textContent = '👍 Good Effort!';
    } else {
        document.getElementById('score-title').textContent = '📚 Review the Material & Try Again!';
    }

    scoreCard.style.display = 'flex';
    renderResults();
    scoreCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function retakeQuiz() {
    state.userAnswers = {};
    state.quizSubmitted = false;
    document.getElementById('quiz-score-card').style.display = 'none';
    renderResults();
}

// Clipboard & Export Utilities
function copyQuestionsToClipboard() {
    if (!state.generatedData || !state.generatedData.questions) return;

    let text = `EduQuestion AI - Assessment Quiz\n`;
    text += `Total Questions: ${state.generatedData.total_questions}\n`;
    text += `=========================================\n\n`;

    state.generatedData.questions.forEach((q, idx) => {
        text += `Q${idx + 1} (${q.type.toUpperCase()}, Difficulty: ${q.difficulty}): ${q.question}\n`;
        if (q.options && q.options.length > 0) {
            q.options.forEach((opt, oIdx) => {
                const letter = String.fromCharCode(65 + oIdx);
                text += `  ${letter}. ${opt}\n`;
            });
        }
        text += `Correct Answer: ${q.answer}\n`;
        text += `Explanation: ${q.explanation || 'N/A'}\n\n`;
    });

    navigator.clipboard.writeText(text).then(() => {
        showToast('All questions copied to clipboard!');
    }).catch(() => {
        showError('Could not copy to clipboard.');
    });
}

function exportJson() {
    if (!state.generatedData) return;
    const jsonStr = JSON.stringify(state.generatedData, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `eduquestion_assessment_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Downloaded JSON file!');
}

// UI Notification Helpers
function showError(msg) {
    const alertBox = document.getElementById('error-alert');
    const textEl = document.getElementById('error-alert-text');
    textEl.textContent = msg;
    alertBox.style.display = 'flex';
    alertBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideError() {
    document.getElementById('error-alert').style.display = 'none';
}

function showToast(message) {
    const toast = document.getElementById('toast-message');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2800);
}

function escapeAttr(str) {
    return String(str).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
