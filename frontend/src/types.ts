export interface Opportunity {
 id:string;title:string;organization:string;description:string;category:string;subcategory:string;location:string;remote:string;host_country:string;host_continent:string;geographic_scope:string[];applicant_coverage:string;eligibility:string;eligibility_evidence:string[];funding_status:string;funding_evidence?:string;source_category?:string;funding_amount:number|null;funding_currency:string|null;salary:string;deadline:string|null;deadline_precision:string;deadline_timezone:string|null;deadline_evidence:string;application_status:string;relevance_score:number;relevance_explanation:string[];tags:string[];skills_not_demonstrated:string[];required_qualifications:string;startup_requirements:string;original_url:string;application_url:string;source_name:string;source_id:string;first_discovered:string;last_verified:string;last_updated:string;link_validation:string;
}
export interface Tracker {saved:boolean;stage:string;notes:string;preparationDeadline:string}
export type Tracking=Record<string,Tracker>;
export interface Source {id:string;name:string;adapter:string;url:string;policy:string;status:string;count:number;message:string;last_success:string|null}
export interface Refresh {status:string;last_attempt:string|null;last_successful_refresh:string|null;active:number;sources:Source[]}
