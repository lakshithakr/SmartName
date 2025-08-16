// src/components/DomainDetails.js

import React, { useEffect, useState } from 'react';
import './DomainDetails.css';

const DomainDetails = () => {
  const [domainDetails, setDomainDetails] = useState(null);

  useEffect(() => {
    const prompt = sessionStorage.getItem("userPrompt");
    const domainName = sessionStorage.getItem("selectedDomain");

    fetch(`${process.env.REACT_APP_API_URL}/details/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ prompt, domain_name: domainName })
    })
      .then((res) => res.json())
      .then((data) => {
        setDomainDetails(data);
      });
  }, []);

  if (!domainDetails) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p className="loading-text">Fetching domain insights...</p>
      </div>
    );
  }

  return (
    <div className="domain-details container py-5">
      <div className="row">
        <div className="col-12">
          <h1 className="domain-title text-center mb-4">{domainDetails.domainName}.lk</h1>

          <hr className="section-divider my-4" />

          <div className="about-domain">
            <h2 className="section-heading mb-3">About {domainDetails.domainName}.lk</h2>
            <p className="domain-description mb-3">
              {domainDetails.domainDescription}
            </p>
          </div>

          <div className="related-fields mb-5">
            <h2 className="section-heading mb-3">Related Fields</h2>
            <ul className="fields-list list-unstyled row">
              {domainDetails.relatedFields.map((field, index) => (
                <li key={index} className="col-md-4 col-sm-6 mb-2">
                  <span className="field-badge">- {field}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="domain-cta mt-4 text-center">
            <a 
              href={`https://register.domains.lk/domains-search?keywords=${domainDetails.domainName}`} 
              className="btn btn-primary domain-link-btn"
              target="_blank"
              rel="noopener noreferrer"
            >
              Proceed
            </a>
            {/* 
            <div className="mt-3">
              <p>
                Loved your domain suggestions?{' '}
                <a
                  href="https://cloud.domains.lk/index.php/apps/forms/s/jnaRpqMsw4kW34w9aQzc9bH7"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="feedback-link"
                >
                  Click here
                </a>{' '}
                to share your feedback and help us improve!
              </p>
            </div> 
            */}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DomainDetails;
