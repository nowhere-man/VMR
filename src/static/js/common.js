/**
 * VMA 公共 JavaScript 组件
 */

// ========== Toast 提示 ==========
let _toastEl = null;

function _getToastEl() {
  if (!_toastEl) {
    _toastEl = document.getElementById('toast');
  }
  return _toastEl;
}

/**
 * 显示 Toast 提示
 * @param {string} message - 提示消息
 * @param {'info'|'success'|'error'} tone - 提示类型
 */
function showToast(message, tone = 'info') {
  const toast = _getToastEl();
  if (!toast) return;
  toast.textContent = message;
  const anchor = 'fixed top-4 right-4 max-w-xs text-sm rounded-lg shadow-lg px-4 py-3 z-50';
  const toneClass =
    tone === 'error'
      ? 'bg-red-600 text-white'
      : tone === 'success'
      ? 'bg-green-600 text-white'
      : 'bg-gray-900 text-white';
  toast.className = `${anchor} ${toneClass}`;
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 2200);
}

// ========== 删除确认弹窗 ==========
let _deletePopover = null;
let _outsideHandler = null;

function _removePopover() {
  if (_deletePopover) {
    _deletePopover.remove();
    _deletePopover = null;
  }
  if (_outsideHandler) {
    document.removeEventListener('click', _outsideHandler, true);
    _outsideHandler = null;
  }
}

/**
 * 显示删除确认弹窗
 * @param {Event} event - 点击事件
 * @param {Object} options - 配置选项
 * @param {string} options.title - 弹窗标题
 * @param {string} options.message - 弹窗消息
 * @param {Function} options.onConfirm - 确认回调
 */
function showDeleteConfirm(event, options) {
  event.preventDefault();
  event.stopPropagation();
  _removePopover();

  const { title = '确认删除？', message = '此操作无法撤销。', onConfirm } = options;

  const btn = event.currentTarget;
  const rect = btn.getBoundingClientRect();
  const pop = document.createElement('div');
  pop.className =
    'fixed bg-white border border-gray-200 rounded-lg shadow-xl p-3 text-sm w-56 z-40';
  pop.innerHTML = `
    <div class="text-gray-900 font-semibold mb-2">${title}</div>
    <p class="text-xs text-gray-600 mb-3">${message}</p>
    <div class="flex items-center justify-end gap-2 text-xs">
      <button class="px-3 py-1 rounded-md border border-gray-300 text-gray-700 hover:bg-gray-100" data-action="cancel">取消</button>
      <button class="px-3 py-1 rounded-md bg-red-600 text-white hover:bg-red-700" data-action="confirm">删除</button>
    </div>
  `;

  // 计算弹窗位置，确保在可视区域内
  const popWidth = 224; // w-56 = 14rem = 224px
  const popHeight = 120; // 估算高度
  const margin = 8;

  let top = rect.bottom + margin;
  let left = rect.left - popWidth + rect.width;

  // 检查右边界
  if (left + popWidth > window.innerWidth - margin) {
    left = window.innerWidth - popWidth - margin;
  }
  // 检查左边界
  if (left < margin) {
    left = margin;
  }
  // 检查下边界，如果超出则显示在按钮上方
  if (top + popHeight > window.innerHeight - margin) {
    top = rect.top - popHeight - margin;
  }
  // 检查上边界
  if (top < margin) {
    top = margin;
  }

  pop.style.top = `${top}px`;
  pop.style.left = `${left}px`;

  pop.addEventListener('click', async (e) => {
    const action = e.target?.dataset?.action;
    if (action === 'cancel') {
      _removePopover();
    }
    if (action === 'confirm') {
      _removePopover();
      if (onConfirm) {
        await onConfirm();
      }
    }
  });

  _outsideHandler = (e) => {
    if (_deletePopover && !_deletePopover.contains(e.target)) {
      _removePopover();
    }
  };
  document.addEventListener('click', _outsideHandler, true);

  document.body.appendChild(pop);
  _deletePopover = pop;
}

// ========== HTML 转义 ==========
/**
 * 转义 HTML 特殊字符
 * @param {string} text - 原始文本
 * @returns {string} 转义后的文本
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
