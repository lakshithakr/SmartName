import React from 'react'
import './About.css'
import AboutImage from '../../Images/about.jpg'
const About = () => {
  return (
    <section className="about">
        <div className="about-content">
            <h2>What Is SmartName?</h2>
            <p>
                <a href="#">SmartName</a> is an AI-powered domain name recommendation system that helps you discover creative, relevant, and impactful domain names. Whether you're starting a business, launching a project, or building a personal brand, SmartName uses advanced natural language processing and machine learning to suggest unique, brandable, and available domain names tailored to your needs. It focuses on delivering names that truly connect with your audience, making the process of finding the perfect domain faster and smarter.
            </p>
        </div>
        <div className="about-image">
            <img src={AboutImage} alt="AI-powered domain system" />
        </div>
  </section>
  )
}

export default About