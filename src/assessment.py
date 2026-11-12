"""Evidence-aware eligibility and research-first prioritization, separate from deadlines."""
import re
from urllib.parse import urlsplit,parse_qs

def identity_key(url):
    p=urlsplit(url)
    if p.hostname and p.hostname.endswith('daad.de'):
        value=parse_qs(p.query).get('phd-id')
        if value:return 'daad:'+value[0]
    return url.rstrip('/')

def apply_assessment(o,profile,weights):
    facts=o.get('assessment',{});conditions=list(facts.get('conditions',[]))
    if facts.get('qualifications'):o['required_qualifications']=facts['qualifications']
    else:
        found=re.search(r'(?:master[’\x27]?s(?: degree)?|bachelor[’\x27]?s(?: degree)?|minimum qualifications|you (?:must|should) (?:have|hold))[^.]{0,220}',o['description'],re.I)
        if found:o['required_qualifications']=found[0].strip()
    o['funding_level']=facts.get('funding_level','unknown')
    o['funding_verified']=bool(facts.get('funding_evidence') and o.get('reviewed_at'))
    o['fully_funded_verified']=o['funding_verified'] and o['funding_level']=='fully_funded'
    if facts.get('funding_evidence'):
        o['funding_evidence']=facts['funding_evidence'];o['funding_status']='funded' if o['funding_level'] in ('fully_funded','funded','paid') else 'unknown'
    if facts.get('salary'):o['salary']=facts['salary']
    if facts.get('application_status'):o['application_status']=facts['application_status']
    o['start_date']=facts.get('start_date');o['intake']=facts.get('intake','unknown')
    o['graduation_compatibility']='needs_confirmation' if o['category']=='research' or o['subcategory']=='internship' else 'not_applicable'
    completion=profile.get('msc_completion','2027-05-31');cutoff=facts.get('degree_completion_by')
    if cutoff and completion>cutoff:
        o['graduation_compatibility']='incompatible';o['eligibility']='restricted'
        o['eligibility_evidence'].append(f'MSc must be completed by {cutoff}; expected completion is May 2027');o['relevance_score']=min(o['relevance_score'],30)
    elif facts.get('degree_in_progress_allowed') and o['start_date'] and o['start_date'][:7]>=completion[:7]:o['graduation_compatibility']='compatible'
    elif facts.get('start_flexible'):conditions.append('Organizer permits start-date flexibility; agree a date after MSc completion')
    if facts.get('language_requirement')=='German C1' and profile.get('languages',{}).get('German','').lower()=='basic':
        o['eligibility']='restricted';o['eligibility_evidence'].append('German C1 required; CV documents basic German');o['relevance_score']=min(o['relevance_score'],30)
    if facts.get('work_authorization_required'):conditions.append('Existing work authorization is required; profile does not establish it')
    if facts.get('startup_required'):
        o['startup_requirements']=facts.get('startup_evidence','A registered startup or project is required; not established in profile');conditions.append(o['startup_requirements'])
    if facts.get('age_requirement'):conditions.append(facts['age_requirement']+'; age not established in sanitized profile')
    o['eligibility_conditions']=list(dict.fromkeys(conditions));o['review_conflicts']=facts.get('conflicts',[]);o['review_status']=facts.get('status_note','')
    o['eligibility_evidence']=list(dict.fromkeys(o['eligibility_evidence']+o['eligibility_conditions']))
    if o['graduation_compatibility']=='compatible':o['relevance_score']=min(100,o['relevance_score']+5)
    if o['fully_funded_verified']:o['relevance_score']=min(100,o['relevance_score']+5)
    if o['eligibility']=='restricted':o['relevance_score']=min(o['relevance_score'],30)
    if facts.get('work_authorization_required') or facts.get('startup_required') or facts.get('specialist_requirements_unverified'):o['relevance_score']=min(o['relevance_score'],69)
    base=o['relevance_score'];research_bonus=12 if o['subcategory']=='PhD' else 9 if o['category']=='research' else 5 if o['subcategory']=='internship' else 0
    regional=5 if any(x in o.get('geographic_scope',[]) for x in ('Rwanda','East Africa')) else 2 if 'Africa' in o.get('geographic_scope',[]) else 0
    cohort=8 if o['graduation_compatibility']=='compatible' and '2027' in o['intake'] else 0
    o['recommendation_score']=min(100,base+research_bonus+regional+cohort+(5 if o['fully_funded_verified'] else 0))
    if o['eligibility']=='restricted':o['recommendation_score']=min(o['recommendation_score'],30)
    if facts.get('work_authorization_required') or facts.get('startup_required') or facts.get('specialist_requirements_unverified'):o['recommendation_score']=min(o['recommendation_score'],69)
    o['recommendation_group']='doctoral' if o['subcategory']=='PhD' else 'research' if o['category']=='research' else 'internship' if o['subcategory']=='internship' else o['category']
    explanations=[]
    if o['subcategory']=='PhD':explanations.append('Doctoral research is a primary career goal')
    if o['fully_funded_verified']:explanations.append('Full funding confirmed in the cited original announcement')
    if o['graduation_compatibility']=='compatible':explanations.append('Published intake permits completion of the MSc before entry')
    if o['graduation_compatibility']=='incompatible':explanations.append('Published degree-completion cutoff conflicts with May 2027 graduation')
    if regional:explanations.append('Regional host location aligns with Rwanda / East Africa discovery preferences; work eligibility remains separate')
    if o['eligibility_conditions']:explanations.append('Confirm the listed eligibility and availability conditions before applying')
    o['relevance_explanation']+=explanations
    return o
