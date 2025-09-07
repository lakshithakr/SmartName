import React from "react";
import "./DomainCard.css";

const DomainCard = ({ domainName }) => {
  const handleClick = () => {
    const url = `https://register.domains.lk/domains-search?keywords=${domainName}`;
    window.open(url, "_blank"); // opens in new tab
  };

  return (
    <div className="card border-dark domain-card" onClick={handleClick}>
      <div className="card-body d-flex flex-column justify-content-between align-items-center">
        <h5 className="card-title">{domainName}.lk</h5>
        <button className="btn btn-success btn-sm">Domain Available</button>
        <p className="load-text mt-2">Click Here to Proceed</p>
      </div>
    </div>
  );
};

export default DomainCard;
