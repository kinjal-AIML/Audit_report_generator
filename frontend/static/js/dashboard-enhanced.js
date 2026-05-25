/* ==============================================
   Mule Detection Dashboard - Enhanced JavaScript
   ============================================== */

// Global state
let _resultsCache = [];
let _networkGraphData = null;
let _sortKey = null;
let _sortDir = 'asc';
let _filterQuery = '';
let _riskDistChart = null;
let _patternChart = null;
let sidebarCollapsed = false;

/* ==============================================
   SIDEBAR FUNCTIONS - KEEP UNCHANGED
   ============================================== */

function togglePatternDetail(patternId) {
    const elem = document.getElementById(patternId);
    if (elem) {
        elem.style.display = elem.style.display === 'none' ? 'block' : 'none';
    }
}

function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const header = section.previousElementSibling;
    
    // Close all other sections
    document.querySelectorAll('.section-content').forEach(s => {
        if (s.id !== sectionId) {
            s.classList.remove('expanded');
            if (s.previousElementSibling) {
                s.previousElementSibling.classList.add('collapsed');
            }
        }
    });
    
    // Toggle current section
    section.classList.toggle('expanded');
    header.classList.toggle('collapsed');
}

function toggleSidebar() {
    const sidebar = document.getElementById('mainSidebar');
    const floatToggle = document.getElementById('sidebarFloatToggle');
    const toggleIcon = document.getElementById('sidebarToggleIcon');
    
    sidebarCollapsed = !sidebarCollapsed;
    
    if (sidebarCollapsed) {
        sidebar.style.marginLeft = '-250px';
        floatToggle.style.left = '10px';
        toggleIcon.classList.remove('fa-chevron-left');
        toggleIcon.classList.add('fa-chevron-right');
    } else {
        sidebar.style.marginLeft = '0';
        floatToggle.style.left = '260px';
        toggleIcon.classList.remove('fa-chevron-right');
        toggleIcon.classList.add('fa-chevron-left');
    }
}

function closeSidebarOnMobile() {
    if (window.innerWidth < 768) {
        document.getElementById('mainSidebar').style.marginLeft = '-250px';
        document.querySelector('.sidebar-overlay').classList.remove('active');
    }
}

function showOpenAIInfo() {
    $('#openaiModal').modal('show');
}

/* ==============================================
   FILE UPLOAD FUNCTIONS
   ============================================== */

document.addEventListener('DOMContentLoaded', function() {
    const browseBtn = document.getElementById('browseBtn');
    const fileInput = document.getElementById('fileInput');
    const runBtn = document.getElementById('runBtn');
    const fileName = document.getElementById('fileName');
    const searchInput = document.getElementById('searchInput');
    
    // Browse button click
    browseBtn.addEventListener('click', function() {
        fileInput.click();
    });
    
    // File selected
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            const file = this.files[0];
            const ext = file.name.split('.').pop().toLowerCase();
            
            if (['csv', 'xlsx', 'xls'].includes(ext)) {
                fileName.innerHTML = `<i class=\\"fas fa-file-excel text-success mr-2\\"></i>${file.name}`;
                runBtn.style.display = 'inline-block';
            } else {
                showToast('Invalid file type. Please upload CSV or Excel file.', 'error');
                fileInput.value = '';
                fileName.textContent = '';
                runBtn.style.display = 'none';
            }
        }
    });
    
    // Run detection
    runBtn.addEventListener('click', function() {
        const file = fileInput.files[0];
        if (!file) {
            showToast('Please select a file first.', 'error');
            return;
        }
        
        uploadAndProcess(file);
    });
    
    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterResultsTable(this.value);
        });
    }
    
    // Initialize first section as expanded
    const firstSection = document.getElementById('patternsSection');
    if (firstSection) {
        firstSection.classList.add('expanded');
    }
});

function uploadAndProcess(file) {
    const progressSection = document.getElementById('progressSection');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const runBtn = document.getElementById('runBtn');
    
    progressSection.style.display = 'block';
    runBtn.disabled = true;
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Simulate progress (in real scenario, use actual progress tracking)
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += 10;
        if (progress <= 90) {
            progressBar.style.width = progress + '%';
            progressBar.textContent = progress + '%';
        }
    }, 200);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        clearInterval(progressInterval);
        progressBar.style.width = '100%';
        progressBar.textContent = '100%';
        
        setTimeout(() => {
            if (data.success) {
                showToast('Detection completed successfully!', 'success');
                updateDashboard(data.data);
                progressSection.style.display = 'none';
                runBtn.disabled = false;
                progressBar.style.width = '0%';
                progressBar.textContent = '0%';
            } else {
                showToast('Error: ' + data.error, 'error');
                progressSection.style.display = 'none';
                runBtn.disabled = false;
            }
        }, 500);
    })
    .catch(error => {
        clearInterval(progressInterval);
        console.error('Upload error:', error);
        showToast('Upload failed. Please try again.', 'error');
        progressSection.style.display = 'none';
        runBtn.disabled = false;
    });
}

/* ==============================================
   DASHBOARD UPDATE FUNCTIONS
   ============================================== */

function updateDashboard(data) {
    const results = data.results || [];
    const stats = data.stats || {};
    
    // Update cache
    _resultsCache = results;
    
    // Update Hero Insight Bar
    updateHeroBar(results, stats);
    
    // Update KPI Cards
    updateKPICards(results, stats);
    
    // Update Charts
    updateCharts(results, stats);
    
    // Update Results Table
    renderResultsTable(results);
    
    // Show all sections
    document.getElementById('heroInsightBar').style.display = 'block';
    document.getElementById('kpiCardsRow').style.display = 'flex';
    document.getElementById('chartRow').style.display = 'flex';
    document.getElementById('resultsRow').style.display = 'block';
    document.getElementById('networkRow').style.display = 'block';
    
    // Initialize network graph
    initNetworkGraph();
}

function updateHeroBar(results, stats) {
    const total = stats.total || 0;
    const high = stats.high || 0;
    
    // Calculate suspicious volume (sum of high and medium risk amounts)
    let suspiciousVolume = 0;
    results.forEach(r => {
        if (r.risk_level === 'CONFIRMED_MULE' || r.risk_level === 'SUSPICIOUS') {
            suspiciousVolume += (parseFloat(r.amount) || 0);
        }
    });
    
    // Find most common pattern
    const patternCounts = {};
    results.forEach(r => {
        if (r.evidence) {
            const patterns = r.evidence.match(/Pattern \\d+/g) || [];
            patterns.forEach(p => {
                patternCounts[p] = (patternCounts[p] || 0) + 1;
            });
        }
    });
    
    let topPattern = '—';
    let maxCount = 0;
    for (const [pattern, count] of Object.entries(patternCounts)) {
        if (count > maxCount) {
            maxCount = count;
            topPattern = pattern;
        }
    }
    
    document.getElementById('heroTotal').textContent = total.toLocaleString();
    document.getElementById('heroHigh').textContent = high.toLocaleString();
    document.getElementById('heroVolume').textContent = '₹' + formatNumber(suspiciousVolume);
    document.getElementById('heroPattern').textContent = topPattern;
}

function updateKPICards(results, stats) {
    const total = stats.total || 0;
    const high = stats.high || 0;
    const medium = stats.medium || 0;
    const flagged = total > 0 ? Math.round(((high + medium) / total) * 100) : 0;
    
    // Calculate average risk score
    let totalScore = 0;
    let scoreCount = 0;
    results.forEach(r => {
        if (r.risk_score && r.risk_score > 0) {
            totalScore += r.risk_score;
            scoreCount++;
        }
    });
    const avgScore = scoreCount > 0 ? Math.round(totalScore / scoreCount) : 0;
    
    // Calculate total suspicious amount
    let totalAmount = 0;
    results.forEach(r => {
        if (r.risk_level === 'CONFIRMED_MULE' || r.risk_level === 'SUSPICIOUS') {
            totalAmount += (parseFloat(r.amount) || 0);
        }
    });
    
    document.getElementById('kpiTotal').textContent = total.toLocaleString();
    document.getElementById('kpiFlagged').textContent = flagged + '%';
    document.getElementById('kpiAvgScore').textContent = avgScore;
    document.getElementById('kpiAmount').textContent = '₹' + formatNumber(totalAmount);
}

function updateCharts(results, stats) {
    const high = stats.high || 0;
    const medium = stats.medium || 0;
    const low = stats.low || 0;
    
    // Risk Distribution Chart
    const riskCtx = document.getElementById('riskDistributionChart');
    if (_riskDistChart) {
        _riskDistChart.destroy();
    }
    
    _riskDistChart = new Chart(riskCtx, {
        type: 'doughnut',
        data: {
            labels: ['High Risk', 'Medium Risk', 'Low Risk'],
            datasets: [{
                data: [high, medium, low],
                backgroundColor: ['#dc3545', '#ffc107', '#27ae60'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
    
    // Pattern Detection Chart (mock data - replace with actual pattern counts)
    const patternCtx = document.getElementById('patternChart');
    if (_patternChart) {
        _patternChart.destroy();
    }
    
    // Count pattern occurrences
    const patternCounts = Array(10).fill(0);
    results.forEach(r => {
        if (r.evidence) {
            for (let i = 1; i <= 10; i++) {
                if (r.evidence.includes(`Pattern ${i}`)) {
                    patternCounts[i - 1]++;
                }
            }
        }
    });
    
    _patternChart = new Chart(patternCtx, {
        type: 'bar',
        data: {
            labels: ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10'],
            datasets: [{
                label: 'Detection Count',
                data: patternCounts,
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

/* ==============================================
   RESULTS TABLE FUNCTIONS
   ============================================== */

function renderResultsTable(results) {
    _resultsCache = results;
    _renderTableRows();
}

function filterResultsTable(query) {
    _filterQuery = query.toLowerCase();
    _renderTableRows();
}

function sortResultsTable(key) {
    if (_sortKey === key) {
        _sortDir = _sortDir === 'asc' ? 'desc' : 'asc';
    } else {
        _sortKey = key;
        _sortDir = 'asc';
    }
    
    // Update sort icons
    document.querySelectorAll('.sort-icon').forEach(icon => {
        icon.className = 'fas fa-sort sort-icon';
    });
    
    const currentHeader = event.target.closest('th');
    const icon = currentHeader.querySelector('.sort-icon');
    icon.className = _sortDir === 'asc' ? 'fas fa-sort-up sort-icon' : 'fas fa-sort-down sort-icon';
    
    _renderTableRows();
}

function _renderTableRows() {
    let filtered = [..._resultsCache];
    
    // Apply filter
    if (_filterQuery) {
        filtered = filtered.filter(r => 
            (r.account_id && r.account_id.toLowerCase().includes(_filterQuery)) ||
            (r.risk_level && r.risk_level.toLowerCase().includes(_filterQuery)) ||
            (r.recommended_action && r.recommended_action.toLowerCase().includes(_filterQuery))
        );
    }
    
    // Apply sort
    if (_sortKey) {
        filtered.sort((a, b) => {
            let valA = a[_sortKey];
            let valB = b[_sortKey];
            
            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();
            
            if (valA < valB) return _sortDir === 'asc' ? -1 : 1;
            if (valA > valB) return _sortDir === 'asc' ? 1 : -1;
            return 0;
        });
    }
    
    const tbody = document.getElementById('resultsTableBody');
    
    if (filtered.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan=\\"7\\" class=\\"text-center text-muted py-5\\">
                    <i class=\\"fas fa-search fa-3x mb-3 d-block\\"></i>
                    No results found.
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = filtered.map(r => {
        const riskBadge = getRiskBadgeClass(r.risk_level);
        const actionBadge = getActionBadgeClass(r.recommended_action);
        const primaryReason = extractPrimaryReason(r.evidence);
        const patternCount = countPatterns(r.evidence);
        
        return `
            <tr onclick=\\"showAccountDetail('${r.account_id}')\\">
                <td><strong>${r.account_id || '—'}</strong></td>
                <td><span class=\\"badge badge-light\\">${r.risk_score || '—'}</span></td>
                <td><span class=\\"badge ${riskBadge}\\">${formatRiskLevel(r.risk_level)}</span></td>
                <td><small>${primaryReason}</small></td>
                <td class=\\"text-center\\"><span class=\\"badge badge-info\\">${patternCount}</span></td>
                <td><span class=\\"badge ${actionBadge}\\">${formatAction(r.recommended_action)}</span></td>
                <td class=\\"text-center\\">
                    <button class=\\"btn btn-sm btn-outline-primary\\" onclick=\\"event.stopPropagation(); showAccountDetail('${r.account_id}');\\">
                        <i class=\\"fas fa-eye\\"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function extractPrimaryReason(evidence) {
    if (!evidence) return '—';
    
    // Try to extract first pattern or key phrase
    const patternMatch = evidence.match(/Pattern \\d+: ([^,\\.]+)/);
    if (patternMatch) {
        return patternMatch[1].substring(0, 40) + '...';
    }
    
    return evidence.substring(0, 40) + '...';
}

function countPatterns(evidence) {
    if (!evidence) return 0;
    const patterns = evidence.match(/Pattern \\d+/g);
    return patterns ? patterns.length : 0;
}

function getRiskBadgeClass(level) {
    const map = {
        'CONFIRMED_MULE': 'badge-confirmed-mule',
        'SUSPICIOUS': 'badge-suspicious',
        'MONITOR': 'badge-monitor',
        'CLEAR': 'badge-clear'
    };
    return map[level] || 'badge-secondary';
}

function getActionBadgeClass(action) {
    const map = {
        'SAR_FILE': 'badge-action-sar',
        'ACCOUNT_FREEZE': 'badge-action-freeze',
        'ENHANCED_MONITORING': 'badge-action-monitor',
        'NO_ACTION': 'badge-action-none',
        'MANUAL_REVIEW': 'badge-action-monitor'
    };
    return map[action] || 'badge-secondary';
}

function formatRiskLevel(level) {
    const map = {
        'CONFIRMED_MULE': 'Confirmed Mule',
        'SUSPICIOUS': 'Suspicious',
        'MONITOR': 'Monitor',
        'CLEAR': 'Clear'
    };
    return map[level] || level;
}

function formatAction(action) {
    const map = {
        'SAR_FILE': 'File SAR',
        'ACCOUNT_FREEZE': 'Freeze',
        'ENHANCED_MONITORING': 'Monitor',
        'NO_ACTION': 'None',
        'MANUAL_REVIEW': 'Review'
    };
    return map[action] || action;
}

/* ==============================================
   ACCOUNT DETAIL FUNCTIONS
   ============================================== */

function showAccountDetail(accountId) {
    const account = _resultsCache.find(r => r.account_id === accountId);
    if (!account) return;
    
    const panel = document.getElementById('accountDetailPanel');
    
    // Update header
    document.getElementById('detailAccountId').textContent = account.account_id;
    document.getElementById('detailRiskBadge').className = 'badge ml-2 ' + getRiskBadgeClass(account.risk_level);
    document.getElementById('detailRiskBadge').textContent = formatRiskLevel(account.risk_level);
    document.getElementById('detailActionBadge').className = 'badge ml-2 ' + getActionBadgeClass(account.recommended_action);
    document.getElementById('detailActionBadge').textContent = formatAction(account.recommended_action);
    document.getElementById('detailRiskScore').textContent = account.risk_score || '—';
    
    // Update AI Summary
    const aiSummary = account.evidence || 'No investigation summary available.';
    document.getElementById('aiSummaryText').textContent = aiSummary;
    
    // Update Score Breakdown
    updateScoreBar('behaviorScoreBar', 'behaviorScoreValue', account.behavior_score || 0);
    updateScoreBar('networkScoreBar', 'networkScoreValue', account.network_score || 0);
    updateScoreBar('contextScoreBar', 'contextScoreValue', account.context_score || 0);
    
    // Update Triggered Patterns
    const patterns = extractPatterns(account.evidence);
    const patternsHtml = patterns.length > 0 
        ? patterns.map(p => `<div class=\\"pattern-chip\\">${p.name} <span class=\\"weight\\">+${p.weight}</span></div>`).join('')
        : '<span class=\\"text-muted\\">No patterns detected</span>';
    document.getElementById('triggeredPatterns').innerHTML = patternsHtml;
    
    // Update Network Metrics
    const subgraph = account.network_subgraph || {};
    document.getElementById('metricFanIn').textContent = subgraph.fan_in || 0;
    document.getElementById('metricFanOut').textContent = subgraph.fan_out || 0;
    document.getElementById('metricLinked').textContent = subgraph.linked_accounts || 0;
    document.getElementById('metricRing').textContent = subgraph.ring_detected ? 'Yes' : 'No';
    
    // Show panel
    panel.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth' });
}

function closeAccountDetail() {
    document.getElementById('accountDetailPanel').style.display = 'none';
}

function updateScoreBar(barId, valueId, score) {
    const bar = document.getElementById(barId);
    const value = document.getElementById(valueId);
    
    const normalizedScore = Math.min(Math.max(score, 0), 100);
    
    bar.style.width = normalizedScore + '%';
    value.textContent = normalizedScore;
    
    // Update color based on score
    if (normalizedScore >= 70) {
        bar.classList.remove('medium', 'low');
        bar.classList.add('high');
    } else if (normalizedScore >= 40) {
        bar.classList.remove('high', 'low');
        bar.classList.add('medium');
    } else {
        bar.classList.remove('high', 'medium');
        bar.classList.add('low');
    }
}

function extractPatterns(evidence) {
    if (!evidence) return [];
    
    const patterns = [];
    const regex = /Pattern (\\d+): ([^,]+)/g;
    let match;
    
    while ((match = regex.exec(evidence)) !== null) {
        patterns.push({
            name: `Pattern ${match[1]}`,
            weight: getPatternWeight(parseInt(match[1]))
        });
    }
    
    return patterns;
}

function getPatternWeight(patternNum) {
    const weights = [15, 30, 20, 20, 15, 25, 20, 30, 20, 10];
    return weights[patternNum - 1] || 10;
}

/* ==============================================
   NETWORK GRAPH FUNCTIONS
   ============================================== */

function initNetworkGraph() {
    fetch('/network-graph')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                _networkGraphData = data.data;
                renderNetworkGraph(data.data);
            } else {
                showNoGraphOverlay();
            }
        })
        .catch(error => {
            console.error('Network graph error:', error);
            showNoGraphOverlay();
        });
}

function renderNetworkGraph(graphData) {
    const { nodes, edges } = graphData;
    
    if (!nodes || nodes.length === 0) {
        showNoGraphOverlay();
        return;
    }
    
    const overlay = document.getElementById('noGraphOverlay');
    if (overlay) overlay.style.display = 'none';
    
    const svg = d3.select('#networkGraphSvg');
    svg.selectAll('*').remove();
    
    const container = document.getElementById('networkGraphContainer');
    const width = container.clientWidth;
    const height = 500;
    
    svg.attr('width', width).attr('height', height);
    
    // Create simulation
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(edges).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(25));
    
    // Create edges
    const link = svg.append('g')
        .selectAll('line')
        .data(edges)
        .enter()
        .append('line')
        .attr('stroke', d => d.is_hub ? '#9b59b6' : '#999')
        .attr('stroke-width', d => Math.max(1, (d.weight || 1) / 10))
        .attr('stroke-opacity', 0.6);
    
    // Create nodes
    const node = svg.append('g')
        .selectAll('circle')
        .data(nodes)
        .enter()
        .append('circle')
        .attr('r', d => d.is_hub ? 12 : 8)
        .attr('fill', d => getNodeColor(d))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .call(d3.drag()
            .on('start', dragStarted)
            .on('drag', dragged)
            .on('end', dragEnded))
        .on('click', (event, d) => {
            showAccountDetail(d.id);
        })
        .on('mouseover', function(event, d) {
            showTooltip(event, d);
        })
        .on('mouseout', hideTooltip);
    
    // Create labels
    const label = svg.append('g')
        .selectAll('text')
        .data(nodes)
        .enter()
        .append('text')
        .text(d => d.id)
        .attr('font-size', 10)
        .attr('dx', 12)
        .attr('dy', 4);
    
    // Update positions on tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        label
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });
    
    function dragStarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragEnded(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

function getNodeColor(node) {
    if (node.is_hub) return '#8e44ad';
    
    const levelColors = {
        'CONFIRMED_MULE': '#dc3545',
        'SUSPICIOUS': '#fd7e14',
        'MONITOR': '#ffc107',
        'CLEAR': '#27ae60'
    };
    
    return levelColors[node.risk_level] || '#6c757d';
}

function showTooltip(event, node) {
    const tooltip = d3.select('body')
        .append('div')
        .attr('class', 'graph-tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0,0,0,0.8)')
        .style('color', 'white')
        .style('padding', '8px 12px')
        .style('border-radius', '6px')
        .style('font-size', '12px')
        .style('pointer-events', 'none')
        .style('z-index', '10000')
        .html(`
            <strong>${node.id}</strong><br>
            Risk: ${node.risk_score || 'N/A'}<br>
            Level: ${formatRiskLevel(node.risk_level)}
        `)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 28) + 'px');
}

function hideTooltip() {
    d3.selectAll('.graph-tooltip').remove();
}

function showNoGraphOverlay() {
    const overlay = document.getElementById('noGraphOverlay');
    if (overlay) overlay.style.display = 'flex';
}

/* ==============================================
   EXPORT FUNCTIONS
   ============================================== */

function downloadCSV() {
    window.location.href = '/reports/csv';
}

function downloadPDFSummary() {
    window.location.href = '/reports/pdf/summary';
}

/* ==============================================
   UTILITY FUNCTIONS
   ============================================== */

function formatNumber(num) {
    if (num >= 10000000) {
        return (num / 10000000).toFixed(2) + ' Cr';
    } else if (num >= 100000) {
        return (num / 100000).toFixed(2) + ' L';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(2) + ' K';
    }
    return num.toFixed(2);
}

function showToast(message, type = 'success') {
    const toastClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
    
    const toast = document.createElement('div');
    toast.className = `toast-notification alert ${toastClass}`;
    toast.innerHTML = `
        <i class=\\"fas ${icon} mr-2\\"></i>
        ${message}
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Enhanced Mule Detection Dashboard loaded');
});
