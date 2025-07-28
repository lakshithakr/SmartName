import React from 'react'
import How_it_work_Image from '../../Images/how_it.jpg'
import './Description.css'
const Description = () => {
  return (
    <section className="description">
        <div className="description-content">
            <h2>How It Works?</h2>
            <p>
                <a href="#">SmartName</a> analyzes the keywords, themes, and context you provide using powerful AI models trained on a rich dataset of web, business, and linguistic patterns. It understands your goals and combines creativity with data-driven insights to generate domain name suggestions. The system evaluates the relevance, uniqueness, and brand appeal of each name, while also checking for domain availability. The result is a curated list of smart, meaningful domain names—ready for you to choose and launch with confidence.
            </p>
        </div>
        <div className="description-image">
            <img src={How_it_work_Image} alt="How It Works" />
        </div>
      </section>
  )
}

export default Description