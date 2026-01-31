// ========== 导航切换 ==========
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // 页面加载时获取新闻
    loadNews();

    // 每 5 分钟自动刷新
    setInterval(() => {
        loadNews();
    }, 5 * 60 * 1000);  // 5 分钟 = 300000 毫秒
});

// ========== 获取来源名称 ==========
function getSourceName(source) {
    const sourceNames = {
        'cankaoxiaoxi': '参考消息',
        'thepaper': '澎湃新闻',
        '36kr': '36氪',
        'wallstreetcn': '华尔街见闻',
        'wallstreetcn_live': '华尔街见闻',
        'wallstreetcn_news': '华尔街见闻',
        'jin10': '金十数据',
        'cls': '财联社',
        'cls_telegraph': '财联社',
        'cls_depth': '财联社',
        'ifeng': '凤凰网',
        'toutiao': '今日头条'
    };
    return sourceNames[source] || source;
}

// ========== 格式化时间（直接显示抓取时间） ==========
function formatTime(isoString) {
    if (!isoString) return '';

    const date = new Date(isoString);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return `${month}-${day} ${hours}:${minutes}`;
}

// ========== 渲染标签 ==========
function renderTags(tags) {
    if (!tags) return '';
    try {
        const tagsArray = typeof tags === 'string' ? JSON.parse(tags) : tags;
        if (!Array.isArray(tagsArray) || tagsArray.length === 0) return '';
        return tagsArray.slice(0, 3).map(tag =>
            `<span class="timeline-tag news-tag">${tag}</span>`
        ).join('');
    } catch (e) {
        return '';
    }
}

// ========== 渲染时间线项（左侧，有 legend） ==========
function renderTimelineItem(article) {
    const timeStr = formatTime(article.timestamp);
    const sourceName = getSourceName(article.source);
    const tagsHtml = renderTags(article.tags);
    // legend 标签
    const legendTag = article.legend
        ? `<span class="timeline-separator news-separator">│</span><span class="timeline-tag news-tag">${article.legend}</span>`
        : '';

    return `
        <div class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="timeline-meta">
                <span class="timeline-source news-source">${sourceName}</span>
                <span class="timeline-separator news-separator">│</span>
                <span class="timeline-time news-time">${timeStr}</span>
                ${legendTag}
                ${tagsHtml}
            </div>
            <h3 class="timeline-title"><a href="${article.url}" target="_blank" style="color: inherit; text-decoration: none;">${article.title}</a></h3>
            <p class="timeline-summary news-summary">${article.summary || article.title}</p>
        </div>
    `;
}

// ========== 渲染热门卡片（右侧，无 legend） ==========
function renderTrendingCard(article) {
    const timeStr = formatTime(article.timestamp);
    const sourceName = getSourceName(article.source);

    return `
        <article class="trending-card" onclick="window.open('${article.url}', '_blank')">
            <h3 class="trending-title">${article.title}</h3>
            <p class="trending-summary news-summary">${article.summary || article.title}</p>
            <div class="trending-meta">
                <span class="trending-source news-source">${sourceName}</span>
                <span class="trending-separator news-separator">│</span>
                <span class="trending-time news-time">${timeStr}</span>
            </div>
        </article>
    `;
}

// ========== 加载新闻（按 legend 分发） ==========
async function loadNews() {
    const timelineCard = document.getElementById('timelineCard');
    const trendingList = document.getElementById('trendingList');

    if (!timelineCard || !trendingList) return;

    try {
        const response = await fetch('/api/articles/latest?limit=50');
        const result = await response.json();

        if (result.code === 200) {
            const articles = result.data || [];

            // 按 legend 字段分发
            const timelineArticles = [];
            const trendingArticles = [];

            articles.forEach(article => {
                if (article.legend) {
                    // 有 legend → 左侧时间线
                    timelineArticles.push(article);
                } else {
                    // 无 legend → 右侧热门
                    trendingArticles.push(article);
                }
            });

            // 渲染左侧时间线
            if (timelineArticles.length > 0) {
                timelineCard.innerHTML = timelineArticles.map(renderTimelineItem).join('');
                // 动态设置背景图 CSS 变量
                const firstLegend = timelineArticles[0].legend || 'musk';
                timelineCard.style.setProperty('--legend-bg',
                    `url('/static/images/legend/${firstLegend}.png')`);
            } else {
                timelineCard.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: var(--maya-meta);">
                        <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
                        <div>暂无奇点人物相关新闻</div>
                    </div>
                `;
                timelineCard.style.setProperty('--legend-bg', 'none');
            }

            // 渲染右侧热门
            if (trendingArticles.length > 0) {
                trendingList.innerHTML = trendingArticles.map(renderTrendingCard).join('');
            } else {
                trendingList.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: var(--maya-meta);">
                        <div>暂无前沿资讯</div>
                    </div>
                `;
            }

        } else {
            console.error('Failed to load articles:', result.message);
        }
    } catch (error) {
        console.error('Failed to load articles:', error);
        timelineCard.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--maya-meta);">
                <div>加载失败，请刷新页面重试</div>
            </div>
        `;
    }
}
