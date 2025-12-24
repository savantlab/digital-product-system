import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

export default function ThematicOverlap() {
  const svgRef = useRef()

  useEffect(() => {
    const width = 600
    const height = 400
    const margin = { top: 20, right: 30, bottom: 60, left: 60 }

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)

    svg.selectAll('*').remove()

    const data = [
      { theme: 'Identity Politics', overlap: 85 },
      { theme: 'Cultural Marxism', overlap: 78 },
      { theme: 'Frankfurt School', overlap: 72 },
      { theme: 'Social Order', overlap: 68 },
      { theme: 'Western Values', overlap: 65 }
    ]

    const x = d3.scaleBand()
      .domain(data.map(d => d.theme))
      .range([margin.left, width - margin.right])
      .padding(0.2)

    const y = d3.scaleLinear()
      .domain([0, 100])
      .range([height - margin.bottom, margin.top])

    const g = svg.append('g')

    // X axis
    g.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x))
      .selectAll('text')
      .attr('fill', '#999')
      .style('text-anchor', 'end')
      .attr('dx', '-.8em')
      .attr('dy', '.15em')
      .attr('transform', 'rotate(-35)')

    // Y axis
    g.append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(5).tickFormat(d => d + '%'))
      .selectAll('text')
      .attr('fill', '#999')

    // Bars with animation
    g.selectAll('rect')
      .data(data)
      .join('rect')
      .attr('x', d => x(d.theme))
      .attr('y', height - margin.bottom)
      .attr('width', x.bandwidth())
      .attr('height', 0)
      .attr('fill', '#667eea')
      .attr('rx', 4)
      .transition()
      .duration(1000)
      .delay((d, i) => i * 100)
      .attr('y', d => y(d.overlap))
      .attr('height', d => height - margin.bottom - y(d.overlap))

    // Value labels
    g.selectAll('.label')
      .data(data)
      .join('text')
      .attr('class', 'label')
      .attr('x', d => x(d.theme) + x.bandwidth() / 2)
      .attr('y', d => y(d.overlap) - 5)
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .attr('font-weight', 600)
      .attr('opacity', 0)
      .text(d => d.overlap + '%')
      .transition()
      .duration(500)
      .delay((d, i) => 1000 + i * 100)
      .attr('opacity', 1)

  }, [])

  return (
    <div className="chart-container">
      <svg ref={svgRef}></svg>
    </div>
  )
}
