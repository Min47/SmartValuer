CREATE TABLE listings_sample (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  listing_id VARCHAR(255) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  address VARCHAR(255) NOT NULL,
  url TEXT NOT NULL,
  availability TEXT DEFAULT NULL,
  project_year INT DEFAULT NULL,
  distance_to_closest_MRT INT DEFAULT NULL,
  description TEXT DEFAULT NULL,
  is_verified_listing BOOLEAN NULL,
  is_everyone_welcomed BOOLEAN NULL,
  listed_date DATE NOT NULL,
  agent_name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  property_type ENUM('condo', 'landed', 'HDB') NOT NULL,
  property_type_text VARCHAR(255) DEFAULT NULL,
  ownership_type ENUM('freehold', 'leasehold') DEFAULT NULL,
  ownership_type_text VARCHAR(255) DEFAULT NULL,
  listing_type ENUM('buy', 'rent') NOT NULL,
  selling_price DOUBLE DEFAULT NULL,
  selling_price_text VARCHAR(255) DEFAULT NULL,
  rent_per_month DOUBLE DEFAULT NULL,
  rent_per_month_text VARCHAR(255) DEFAULT NULL,
  unit_type ENUM('room', 'studio', 'house') NOT NULL,
  bedroom_count INT DEFAULT NULL,
  bathroom_count INT DEFAULT NULL,
  floor_size_sqft INT DEFAULT NULL,
  land_size_sqft INT DEFAULT NULL,
  psf_floor DOUBLE DEFAULT NULL,
  psf_land DOUBLE DEFAULT NULL
);

# -----

SELECT
	*
FROM
	listings_sample l
	
# -----
	
DROP TABLE listings_sample
	
# -----
	
INSERT
	INTO
	listings_sample (
	listing_id,
	title,
	address,
	url,
	availability,
	project_year,
	distance_to_closest_MRT,
	description,
	is_verified_listing,
	is_everyone_welcomed,
	listed_date,
	agent_name,
	created_at,
	property_type,
	property_type_text,
	ownership_type,
	ownership_type_text,
	listing_type,
	selling_price,
	selling_price_text,
	rent_per_month,
	rent_per_month_text,
	unit_type,
	bedroom_count,
	bathroom_count,
	floor_size_sqft,
	land_size_sqft,
	psf_floor,
	psf_land)
VALUES (
'ID000001',
'Sample Property 1',
'58 Example Street',
'https://www.propertyguru.com.sg/listing/for-rent-sample-property-1',
'Ready to Move',
'2024',
'1500',
'Beautiful property with 3 bedrooms and excellent amenities.',
TRUE,
TRUE,
'2024-06-26',
'Agent 1',
'2025-04-15 11:55:50',
'landed',
'Bungalow House',
'leasehold',
NULL,
'rent',
'3000000',
'S$ 1,000,000',
NULL,
NULL,
'studio',
'0',
NULL,
NULL,
'2000',
'3.5',
NULL);
