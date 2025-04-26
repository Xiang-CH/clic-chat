import { Citation } from "./citation";

interface Ordinance {
  cap_no: string;
  section_no: string;
  cap_title: string;
  section_heading: string;
  text: string;
  url: string;
  _relevance_score?: number;
  _distance?: number;
}

interface Judgement {
  case_name: string;
  court: string;
  date: string;
  case_summary: string;
  case_causes: string;
  court_decision: string;
  url: string;
  _relevance_score?: number;
  _distance?: number;
}

export interface Groundings {
  ordinances: Ordinance[];
  judgements: Judgement[];
}


export const GroundingsDisplay = ({ groundings }: { groundings: Groundings }) => {
  return (
    <div className="flex flex-col gap-4 w-full">
      {groundings.ordinances.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-2">Ordinances & Regulations</h3>
          <div className="space-y-3">
            {groundings.ordinances.map((ord, index) => (
              <div key={index} className="p-3 bg-muted/50 rounded-lg">
                <h4 className="font-medium">
                  Cap {ord.cap_no} ({ord.cap_title}), {ord.cap_no.endsWith('A') ? 'Regulation' : 'Section'} {ord.section_no}
                  {ord.section_heading && ` - ${ord.section_heading}`}
                </h4>
                <p className="mt-1 text-sm max-h-72 text-ellipsis overflow-auto">{ord.text}</p>
                <p className="mt-1 text-xs text-muted-foreground">Score: {ord._relevance_score? ord._relevance_score.toFixed(2) : ord._distance?.toFixed(2)}</p>
                <Citation title={`Cap ${ord.cap_no}, Section ${ord.section_no}`} url={ord.url} />
              </div>
            ))}
          </div>
        </div>
      )}

      {groundings.judgements.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-2">Judgements & Cases</h3>
          <div className="space-y-3">
            {groundings.judgements.map((judge, index) => (
              <div key={index} className="p-3 bg-muted/50 rounded-lg">
                <h4 className="font-medium">
                  {judge.date}: {judge.case_name} ({judge.court})
                </h4>
                <p className="mt-1 text-sm">{judge.case_summary}</p>
                <div className="mt-2 text-sm flex flex-col gap-1">
                  <p><span className="font-bold">Case Causes:</span> {judge.case_causes}</p>
                  <p><span className="font-bold">Court Decision:</span> {judge.court_decision}</p>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">Score: {judge._relevance_score? judge._relevance_score.toFixed(2) : judge._distance?.toFixed(2)}</p>
                <Citation title={judge.case_name} url={judge.url} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};