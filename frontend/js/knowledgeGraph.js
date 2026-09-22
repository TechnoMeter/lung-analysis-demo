// frontend/js/knowledgeGraph.js

let networkInstance = null;
const graphContainer = document.getElementById('vis-graph-container');
const graphOverlay = document.getElementById('graph-overlay');
const studyTitle = document.getElementById('graph-study-title');
const statCount = document.getElementById('g-stat-count');
const statActive = document.getElementById('g-stat-active');
let currentSeriesUid = '';

/**
 * Universal clipboard copy helper with visual feedback
 */
export function copyTextToClipboard(text, btnElement) {
  if (!navigator.clipboard || !text) return;
  navigator.clipboard.writeText(text).then(() => {
    const originalText = btnElement.innerHTML;
    btnElement.innerHTML = '✓ Copied!';
    btnElement.classList.add('copied');
    setTimeout(() => {
      btnElement.innerHTML = originalText;
      btnElement.classList.remove('copied');
    }, 1800);
  }).catch((err) => console.error('Copy failed:', err));
}

export async function showKnowledgeGraph(seriesuid, selectedFindingId = null, onSelectFinding = null) {
  graphOverlay.classList.remove('hidden');
  currentSeriesUid = seriesuid;
  studyTitle.textContent = `Study: ${seriesuid}`;

  // Attach graph copy button handler
  const copyBtn = document.getElementById('btn-copy-graph-uid');
  if (copyBtn) {
    copyBtn.onclick = () => copyTextToClipboard(currentSeriesUid, copyBtn);
  }

  try {
    const response = await fetch(`/api/v1/graph?seriesuid=${encodeURIComponent(seriesuid)}`);
    if (!response.ok) throw new Error(`Graph API returned HTTP ${response.status}`);
    const graphData = await response.json();

    const findingNodes = graphData.nodes.filter(
      (n) => n.group === 'finding' || (typeof n.id === 'string' && n.id.startsWith('F-'))
    );
    if (statCount) statCount.textContent = findingNodes.length.toString();
    if (statActive) statActive.textContent = selectedFindingId || (findingNodes[0]?.id || 'None');

    renderVisNetwork(graphData, seriesuid, selectedFindingId, onSelectFinding);
  } catch (err) {
    console.error('Failed to load relational knowledge graph:', err);
    studyTitle.textContent = `Error loading graph: ${err.message}`;
  }
}

export function hideKnowledgeGraph() {
  graphOverlay.classList.add('hidden');
}

function renderVisNetwork(graphData, seriesuid, selectedFindingId, onSelectFinding) {
  if (networkInstance) {
    networkInstance.destroy();
    networkInstance = null;
  }

  const clusterTitles = {
    0: 'Right Lung Typical',
    1: 'High-Volume Masses',
    2: 'Left Lung Typical',
    3: 'Axial Couch Outliers'
  };

  // Safe shallow clones
  const nodes = graphData.nodes.map((n) => ({ ...n }));
  const edges = graphData.edges.map((e) => ({ ...e }));

  // Locate active finding for State 4 morphometric and guideline branch
  const activeNode = nodes.find((n) => n.id === selectedFindingId);

  if (activeNode) {
    const diameter = activeNode.value || 0;
    const rawTitle = typeof activeNode.title === 'string' ? activeNode.title : '';
    const volMatch = rawTitle.match(/Volume:\s*([0-9.]+)/i);
    const volume = volMatch ? parseFloat(volMatch[1]) : (Math.PI / 6) * Math.pow(diameter || 1, 3);
    const isFleischnerHigh = diameter >= 8.0;

    const dimNodeId = `dim_${selectedFindingId}`;
    const fleischnerNodeId = `fleischner_${selectedFindingId}`;

    if (!nodes.some((n) => n.id === dimNodeId)) {
      nodes.push({
        id: dimNodeId,
        group: 'dimension',
        level: 2,
        shape: 'box',
        label: `MORPHOMETRICS\n${diameter.toFixed(1)} mm • ${Math.round(volume).toLocaleString()} mm³`,
        title: `Physical Diameter: ${diameter.toFixed(1)} mm\nDerived Volume: ${volume.toFixed(1)} mm³`,
        margin: 8,
        color: {
          background: '#090d16',
          border: '#38bdf8',
          highlight: { background: '#0f172a', border: '#38bdf8' }
        },
        font: { color: '#38bdf8', face: 'system-ui, sans-serif', size: 10, bold: true, multi: true },
        borderWidth: 1.5
      });

      edges.push({
        from: selectedFindingId,
        to: dimNodeId,
        color: { color: '#f43f5e' },
        arrows: { to: { enabled: true, scaleFactor: 0.7 } },
        smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.4 },
        width: 2
      });
    }

    if (!nodes.some((n) => n.id === fleischnerNodeId)) {
      nodes.push({
        id: fleischnerNodeId,
        group: 'fleischner',
        level: 3,
        shape: 'box',
        label: isFleischnerHigh
          ? 'FLEISCHNER GUIDELINE\n≥8mm High Risk (Biopsy / HRCT)'
          : 'FLEISCHNER GUIDELINE\n<8mm Low Risk (Routine Follow-up)',
        title: isFleischnerHigh
          ? 'Fleischner Society: High clinical risk requires high-resolution CT follow-up or biopsy'
          : 'Fleischner Society: Low clinical risk warrants standard routine follow-up',
        margin: 8,
        color: {
          background: isFleischnerHigh ? '#1e0c14' : '#06130e',
          border: isFleischnerHigh ? '#f43f5e' : '#10b981',
          highlight: { background: '#0f172a', border: '#38bdf8' }
        },
        font: {
          color: isFleischnerHigh ? '#ff4d6d' : '#34d399',
          face: 'system-ui, sans-serif',
          size: 10,
          bold: true,
          multi: true
        },
        borderWidth: 1.5
      });

      edges.push({
        from: dimNodeId,
        to: fleischnerNodeId,
        color: { color: isFleischnerHigh ? '#f43f5e' : '#10b981' },
        arrows: { to: { enabled: true, scaleFactor: 0.7 } },
        smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.4 },
        width: 2
      });
    }
  }

  // Style and guarantee explicit hierarchical levels across all nodes
  const styledNodes = nodes.map((node) => {
    const isChosen = node.id === selectedFindingId;
    const rawTitle = typeof node.title === 'string' ? node.title : '';
    const plainTooltip = rawTitle
      .replace(/<br\s*[\/]?>/gi, '\n')
      .replace(/<[^>]*>/g, '')
      .trim();

    // LEVEL 0: Study Session
    if (node.group === 'study' || node.id === seriesuid) {
      const shortUid = node.id.length > 28 ? `${node.id.substring(0, 16)}...${node.id.slice(-8)}` : node.id;
      return {
        ...node,
        level: 0,
        shape: 'box',
        label: `CT STUDY ACQUISITION\n${shortUid}`,
        title: plainTooltip || `Study UID:\n${node.id}`,
        margin: 12,
        color: {
          background: '#0a101d',
          border: '#38bdf8',
          highlight: { background: '#0f172a', border: '#38bdf8' }
        },
        font: { color: '#f8fafc', face: 'Consolas, monospace', size: 12, bold: true, multi: true },
        borderWidth: 2,
        shadow: { enabled: true, color: 'rgba(56, 189, 248, 0.35)', size: 12 }
      };
    }

    // LEVEL 1: Findings
    if (node.group === 'finding' || (typeof node.id === 'string' && node.id.startsWith('F-'))) {
      return {
        ...node,
        level: 1,
        shape: 'box',
        label: isChosen ? `★ ACTIVE FOCUS\n${node.id}` : `FINDING\n${node.id}`,
        title: plainTooltip || `Finding: ${node.id}`,
        margin: 10,
        color: {
          background: isChosen ? '#200d18' : '#0e1626',
          border: isChosen ? '#f43f5e' : '#818cf8',
          highlight: { background: isChosen ? '#2d1121' : '#1e293b', border: '#ffffff' }
        },
        font: { color: '#f8fafc', face: 'Consolas, monospace', size: 12, bold: true, multi: true },
        borderWidth: isChosen ? 2.5 : 1.5,
        shadow: { enabled: isChosen, color: 'rgba(244, 63, 94, 0.5)', size: 16 }
      };
    }

    // LEVEL 2: K-Means Cohorts
    if (node.group === 'cluster' || (typeof node.id === 'string' && node.id.startsWith('cluster'))) {
      const match = node.id.match(/\d+/);
      const cId = match ? parseInt(match[0], 10) : 0;
      const cName = clusterTitles[cId] || `Cluster ${cId}`;

      return {
        ...node,
        level: 2,
        shape: 'box',
        label: `COHORT PROFILE\nCluster ${cId}: ${cName}`,
        title: plainTooltip || `K-Means Assigned Group ${cId}: ${cName}`,
        margin: 10,
        color: {
          background: '#1c1708',
          border: '#fbbf24',
          highlight: { background: '#29220c', border: '#f59e0b' }
        },
        font: { color: '#fef3c7', face: 'system-ui, sans-serif', size: 11, bold: true, multi: true },
        borderWidth: 2,
        shadow: { enabled: true, color: 'rgba(251, 191, 36, 0.3)', size: 10 }
      };
    }

    // Already styled dimension & fleischner branches
    if (node.group === 'dimension' || node.group === 'fleischner') {
      return node;
    }

    // LEVEL 3: Outlier Flags
    const rawLabel = (node.label || '').trim();
    const scoreMatch = rawLabel.match(/([0-9.]+)/);
    const scoreVal = scoreMatch ? parseFloat(scoreMatch[1]) : 0.0;
    const isOutlier = scoreVal >= 0.40;

    return {
      ...node,
      level: 3,
      shape: 'box',
      label: isOutlier ? `ANOMALY STATUS\nHigh Outlier (${scoreVal.toFixed(2)})` : `ANOMALY STATUS\nTypical (${scoreVal.toFixed(2)})`,
      title: plainTooltip || `Normalized Euclidean Centroid Distance: ${scoreVal.toFixed(3)}`,
      margin: 8,
      color: {
        background: isOutlier ? '#1e0c14' : '#090d16',
        border: isOutlier ? '#f43f5e' : '#10b981',
        highlight: { background: '#0f172a', border: '#38bdf8' }
      },
      font: { color: isOutlier ? '#ff4d6d' : '#34d399', face: 'system-ui, sans-serif', size: 10, bold: true, multi: true },
      borderWidth: 1.5
    };
  });

  // Edge styling
  const styledEdges = edges.map((edge) => {
    const isConnectedToChosen = edge.from === selectedFindingId || edge.to === selectedFindingId;
    return {
      ...edge,
      label: undefined,
      color: {
        color: isConnectedToChosen ? '#f43f5e' : 'rgba(100, 116, 139, 0.35)',
        highlight: '#38bdf8',
        hover: '#38bdf8'
      },
      arrows: { to: { enabled: true, scaleFactor: 0.7 } },
      smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.4 },
      width: isConnectedToChosen ? 2.5 : 1.2
    };
  });

  const data = {
    nodes: new vis.DataSet(styledNodes),
    edges: new vis.DataSet(styledEdges)
  };

  const options = {
    layout: {
      hierarchical: {
        enabled: true,
        direction: 'UD',
        sortMethod: 'directed',
        levelSeparation: 120,
        nodeSpacing: 220,
        treeSpacing: 240,
        blockShifting: true,
        edgeMinimization: true
      }
    },
    physics: {
      hierarchicalRepulsion: {
        nodeDistance: 190,
        springLength: 100,
        springConstant: 0.05
      }
    },
    interaction: {
      hover: true,
      tooltipDelay: 60,
      zoomView: true,
      dragView: true
    }
  };

  networkInstance = new vis.Network(graphContainer, data, options);

  networkInstance.once('stabilizationIterationsDone', () => {
    if (selectedFindingId) {
      networkInstance.focus(selectedFindingId, {
        scale: 1.1,
        animation: { duration: 700, easingFunction: 'easeInOutQuad' }
      });
    } else {
      networkInstance.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
    }
  });

  networkInstance.on('click', (params) => {
    if (params.nodes.length > 0) {
      const clickedId = params.nodes[0];
      if (typeof clickedId === 'string' && clickedId.startsWith('F-')) {
        if (onSelectFinding) onSelectFinding(clickedId);
      }
    }
  });

  networkInstance.on('doubleClick', () => {
    networkInstance.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
  });
}