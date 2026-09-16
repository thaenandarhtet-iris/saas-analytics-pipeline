-- Staging: 1:1 with raw customers table
-- No transformations, just cleaning and type casting

with source as (
    select 
        customer_id,
        company_name,
        industry,
        region,
        employee_size_band,
        cast(signup_date as date) as signup_date
    from {{ source('raw', 'customers') }}
)

select * from source
