import json
import random
from datetime import datetime, timedelta

class KeyEventGenerator:
    def __init__(self,
                 x_range=(213, 3671),
                 y_range=(89.5, 200),
                 z_range=(-2879, -358),
                 start_time="2025-01-01T00:00:00",
                 end_time="2025-01-01T00:01:00",
                 events_per_type=3):
        """
        Key Event 생성기
        
        Parameters:
        -----------
        x_range : tuple
            X축 범위 (min, max)
        y_range : tuple
            Y축 범위 (min, max) - 높이
        z_range : tuple
            Z축 범위 (min, max)
        start_time : str
            시작 시간 (ISO 8601 형식)
        end_time : str
            종료 시간 (ISO 8601 형식)
        events_per_type : int
            이벤트 타입당 생성할 이벤트 수
        """
        self.x_range = x_range
        self.y_range = y_range
        self.z_range = z_range
        self.start_time = datetime.fromisoformat(start_time)
        self.end_time = datetime.fromisoformat(end_time)
        self.events_per_type = events_per_type
        
        # 이벤트 타입
        self.event_types = ["collision", "cluster", "pass_out"]
    
    def _random_timestamp(self):
        """무작위 타임스탬프 생성 (초 단위까지만)"""
        time_diff = (self.end_time - self.start_time).total_seconds()
        random_seconds = random.uniform(0, time_diff)
        timestamp = self.start_time + timedelta(seconds=random_seconds)
        # 밀리초 제거
        timestamp = timestamp.replace(microsecond=0)
        return timestamp.isoformat()
    
    def _random_location(self):
        """무작위 위치 생성"""
        return {
            "x": round(random.uniform(*self.x_range), 1),
            "y": round(random.uniform(*self.y_range), 1),
            "z": round(random.uniform(*self.z_range), 1)
        }
    
    def generate_event(self, event_type):
        """단일 이벤트 생성"""
        return {
            "type": event_type,
            "timestamp": self._random_timestamp(),
            "location": self._random_location()
        }
    
    def generate(self):
        """모든 이벤트 생성"""
        events = []
        
        for event_type in self.event_types:
            for _ in range(self.events_per_type):
                events.append(self.generate_event(event_type))
        
        # 타임스탬프 기준으로 정렬
        events.sort(key=lambda x: x['timestamp'])
        
        return {
            "metadata": {
                "building_bounds": {
                    "x_range": list(self.x_range),
                    "y_range": list(self.y_range),
                    "z_range": list(self.z_range)
                },
                "time_range": {
                    "start": self.start_time.isoformat(),
                    "end": self.end_time.isoformat()
                },
                "total_events": len(events),
                "event_types": {
                    "collision": self.events_per_type,
                    "cluster": self.events_per_type,
                    "pass_out": self.events_per_type
                }
            },
            "events": events
        }
    
    def save_to_json(self, filename="key_events.json", indent=2):
        """JSON 파일로 저장"""
        data = self.generate()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return data


# 사용 예시
if __name__ == "__main__":
    # 예시 1: 기본 설정 (1분, 각 타입당 3개 이벤트)
    print("예시 1: 기본 설정 (1분, 각 타입당 3개)")
    generator = KeyEventGenerator()
    data1 = generator.save_to_json("key_events_1min.json")
    
    print(f"생성된 이벤트: {data1['metadata']['total_events']}개")
    print("\n생성된 이벤트 목록:")
    for event in data1['events']:
        print(f"  [{event['timestamp']}] {event['type']:12s} at ({event['location']['x']}, {event['location']['y']}, {event['location']['z']})")
    print(f"\n파일 저장: key_events_1min.json")
    print("\n" + "="*80 + "\n")
    
    # # 예시 2: 긴 시간 범위 (1시간, 각 타입당 10개 이벤트)
    # print("예시 2: 1시간, 각 타입당 10개")
    # generator2 = KeyEventGenerator(
    #     start_time="2025-01-01T00:00:00",
    #     end_time="2025-01-01T01:00:00",
    #     events_per_type=10
    # )
    # data2 = generator2.save_to_json("key_events_1hour.json")
    
    # print(f"생성된 이벤트: {data2['metadata']['total_events']}개")
    # print("\n처음 5개 이벤트:")
    # for event in data2['events'][:5]:
    #     print(f"  [{event['timestamp']}] {event['type']:12s} at ({event['location']['x']}, {event['location']['y']}, {event['location']['z']})")
    # print(f"\n파일 저장: key_events_1hour.json")
    # print("\n" + "="*80 + "\n")
    
    # # 예시 3: 사용자 정의 범위
    # print("예시 3: 사용자 정의 시간 범위")
    # generator3 = KeyEventGenerator(
    #     start_time="2025-01-01T09:00:00",
    #     end_time="2025-01-01T18:00:00",  # 9시간 (근무시간)
    #     events_per_type=5
    # )
    # data3 = generator3.save_to_json("key_events_workday.json")
    
    # print(f"생성된 이벤트: {data3['metadata']['total_events']}개")
    # print("\n이벤트 타입별 분포:")
    # event_counts = {}
    # for event in data3['events']:
    #     event_type = event['type']
    #     event_counts[event_type] = event_counts.get(event_type, 0) + 1
    # for event_type, count in event_counts.items():
    #     print(f"  {event_type}: {count}개")
    # print(f"\n파일 저장: key_events_workday.json")
    
    # # JSON 구조 예시 출력
    # print("\n" + "="*80)
    # print("JSON 구조 예시:")
    # print("="*80)
    # print(json.dumps(data1, indent=2, ensure_ascii=False))