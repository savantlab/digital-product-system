import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

export default function SemanticSimilarity() {
  const svgRef = useRef()

  useEffect(() => {
    const width = 600
    const height = 400
    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)

    // Clear previous content
    svg.selectAll('*').remove()

    const data = [
      { source: 'Peterson', target: 'Breivik', similarity: 16 },
      { source: 'Peterson', target: 'Marx', similarity: 45 },
      { source: 'Breivik', target: 'Marx', similarity: 38 }
    ]

    // Create force simulation
    const nodes = [
      { id: 'Peterson', group: 1 },
      { id: 'Breivik', group: 2 },
      { id: 'Marx', group: 3 }
    ]

    const links = data.map(d => ({
      source: d.source,
      target: d.target,
      value: d.similarity
    }))

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))

    // Draw links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#667eea')
      .attr('stroke-width', d => d.value / 5)
      .attr('stroke-opacity', 0.6)

    // Draw link labels
    const linkLabel = svg.append('g')
      .selectAll('text')
      .data(links)
      .join('text')
      .attr('fill', '#999')
      .attr('font-size', 12)
      .attr('text-anchor', 'middle')
      .text(d => `${d.value}%`)

    // Draw nodes
    const node = svg.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', 30)
      .attr('fill', d => d.group === 1 ? '#667eea' : d.group === 2 ? '#764ba2' : '#48bb78')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)

    // Node labels
    const nodeLabel = svg.append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 5)
      .attr('fill', '#fff')
      .attr('font-weight', 600)
      .attr('font-size', 14)
      .text(d => d.id)

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)

      linkLabel
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2)

      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y)

      nodeLabel
        .attr('x', d => d.x)
        .attr('y', d => d.y)
    })

    return () => simulation.stop()
  }, [])

  return (
    <div className="chart-container">
      <svg ref={svgRef}></svg>
    </div>
  )
}
