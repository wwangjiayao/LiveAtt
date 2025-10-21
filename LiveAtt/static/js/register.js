// 文件顶部，声明一个全局变量
let membersData = [];

// DOM
const registerContainer = document.getElementById('registerContainer');
const emptyState = document.getElementById('emptyState');
const memberCount = document.getElementById('memberCount');
const syncButton = document.getElementById('syncMembers');
const clearButton = document.getElementById('clearRegister');
const registrationStatus = document.getElementById('registrationStatus');
let currentPage = 1;
const itemsPerPage = 6; // 每页6个

// 添加CSS样式（可以放在HTML的<style>标签中）
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  .card-image {
    width: 150px;
    height: 150px;
    object-fit: cover;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
  }

  .student-id {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px; /* 根据实际表格宽度调整 */
}


  .card-image:hover {
    transform: scale(1.05);
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    padding: 20px;
  }

  .card {
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    overflow: hidden;
    transition: all 0.3s ease;
  }

  .card:hover {
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    transform: translateY(-4px);
  }

  .card-header {
    display: flex;
    align-items: center;
    padding: 16px;
    gap: 16px;
  }

  .card-body {
    padding: 0 16px 16px;
    color: #666;
  }

  .pagination {
    display: flex;
    justify-content: center;
    margin: 24px 0;
    gap: 12px;
  }

  .page-btn {
    padding: 8px 16px;
    border: 1px solid #ddd;
    border-radius: 6px;
    background-color: white;
    cursor: pointer;
    transition: all 0.2s;
  }

  .page-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .page-btn:not(:disabled):hover {
    background-color: #f5f5f5;
    border-color: #ccc;
  }

  .page-info {
    display: flex;
    align-items: center;
    font-weight: 500;
  }
`;
document.head.appendChild(styleSheet);

function showStatus(msg, isError = false) {
  registrationStatus.textContent = msg;
  registrationStatus.style.color = isError ? '#e74c3c' : '#2ecc71';
  registrationStatus.style.display = 'block';
  setTimeout(() => registrationStatus.style.display = 'none', 3000);
}

function renderMembers(members) {
  // —— 先清除旧的卡片、旧的网格和旧的分页 —— //
  // 删除所有 .grid
  registerContainer.querySelectorAll('.grid').forEach(el => el.remove());
  // 删除所有 .pagination
  registerContainer.querySelectorAll('.pagination').forEach(el => el.remove());
  // 保留 emptyState，不需要专门移除单个 card

  memberCount.textContent = members.length;
  if (!members.length) {
    emptyState.style.display = 'flex';
    return;
  }
  emptyState.style.display = 'none';

  // 计算分页
  const totalPages = Math.ceil(members.length / itemsPerPage);
  currentPage = Math.min(currentPage, totalPages);

  // 当前页要展示的数据
  const start = (currentPage - 1) * itemsPerPage;
  const pageItems = members.slice(start, start + itemsPerPage);

  // 构造新的网格
  const grid = document.createElement('div');
  grid.className = 'grid';
  pageItems.forEach(m => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <div class="card-header">
        <img
          src="${m.avatar}"
          alt="${m.name}"
          class="card-image"
          onerror="this.src='https://picsum.photos/200/200?random=${m.studentId}'"
        >
        <div>
          <h4>${m.name}</h4>
          <p>${m.studentId}</p>
        </div>
      </div>`;
    grid.appendChild(card);
  });
  registerContainer.appendChild(grid);

  // 只有超过一页才加分页
  if (totalPages > 1) {
    registerContainer.appendChild(createPagination(totalPages));
  }
}

function createPagination(totalPages) {
  const pag = document.createElement('div');
  pag.className = 'pagination';

  const prev = document.createElement('button');
  prev.className = 'page-btn';
  prev.innerHTML = '<i class="fas fa-chevron-left"></i>';
  prev.disabled = currentPage === 1;
  prev.onclick = () => {
    if (currentPage > 1) {
      currentPage--;
      renderMembers(membersData);
    }
  };

  const next = document.createElement('button');
  next.className = 'page-btn';
  next.innerHTML = '<i class="fas fa-chevron-right"></i>';
  next.disabled = currentPage === totalPages;
  next.onclick = () => {
    if (currentPage < totalPages) {
      currentPage++;
      renderMembers(membersData);
    }
  };

  const info = document.createElement('span');
  info.className = 'page-info';
  info.textContent = `${currentPage} / ${totalPages}`;

  pag.append(prev, info, next);
  return pag;
}

async function fetchMembers() {
  showStatus('同步中...');
  try {
    const res = await fetch('/api/members');
    const json = await res.json();
    if (json.success) {
      membersData = json.data;        // 存缓存
      currentPage = 1;                // 重置页码
      renderMembers(membersData);
      showStatus(`已同步 ${json.count} 名成员`);
    } else {
      showStatus(json.message || '同步失败', true);
    }
  } catch {
    showStatus('网络错误，无法同步', true);
  }
}

async function registerMembers() {
  showStatus('注册中...');
  try {
    const res = await fetch('/api/members/register', { method:'POST' });
    const json = await res.json();
    if (json.success) {
      showStatus(`成功注册 ${json.count} 名成员`);
      currentPage = 1;
      fetchMembers();
    } else {
      showStatus(json.message || '注册失败', true);
    }
  } catch (e) {
    showStatus('网络错误，无法注册', true);
  }
}

function clearMembers() {
  if (confirm('确认清空？')) {
    renderMembers([]);
    showStatus('已清空');
  }
}

// 事件绑定
document.getElementById('registerMembers').addEventListener('click', registerMembers);
syncButton.addEventListener('click', fetchMembers);
clearButton.addEventListener('click', clearMembers);

document.addEventListener('DOMContentLoaded', () => {
  renderMembers([]);
  // 空状态图标动画
  const icon = emptyState.querySelector('i');
  setInterval(()=>{
    icon.style.transform='scale(1.1) rotate(5deg)';
    setTimeout(()=>icon.style.transform='none',300);
  },3000);
});