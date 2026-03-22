from manim import *
import os
import json


class IntroductionScene(Scene):
    def construct(self):
        # Default content
        title_text = "视频自动化创作平台"
        subtitle_text = "Automated Video Creation Platform"
        features_list = [
            "1. 数据驱动 (Data Driven)",
            "2. 自动排版 (Auto Layout)",
            "3. 多平台适配 (Multi-Platform)",
            "4. 批量生成 (Batch Processing)"
        ]
        logo_label_text = "Logo"
        conclusion_text = "感谢观看"

        # Try to load screenplay override
        screenplay_path = os.environ.get("SCREENPLAY_PATH")
        if screenplay_path and os.path.exists(screenplay_path):
            try:
                with open(screenplay_path, "r", encoding="utf-8") as f:
                    sp_data = json.load(f)
                    scenes = sp_data.get("scenes", [])
                    
                    # Refined Mapping Strategy:
                    # Scene 1: Title & Subtitle.
                    if len(scenes) >= 1:
                        # Use Visual Content for Title
                        # Use Narration for Subtitle (truncated)
                        s = scenes[0]
                        v = s.get("visuals", [])
                        if v and v[0].get("type") == "text":
                            title_text = v[0].get("content")
                        if s.get("narration"):
                            subtitle_text = s.get("narration")[:30] + "..." if len(s.get("narration")) > 30 else s.get("narration")

                    # Scene 2: Features
                    if len(scenes) >= 2:
                        s = scenes[1]
                        v = s.get("visuals", [])
                        if v and v[0].get("type") == "text":
                            # Treat the content as a single feature or split by punctuation?
                            # For simplicity, just display the content as one big text
                            features_list = [v[0].get("content")]
                        elif s.get("narration"):
                             features_list = [s.get("narration")]
                    
                    # Scene 3: Logo/Climax Visual
                    if len(scenes) >= 3:
                        s = scenes[2]
                        v = s.get("visuals", [])
                        if v and v[0].get("type") == "text":
                             logo_label_text = v[0].get("content")

                    # Scene 4: Conclusion
                    if len(scenes) >= 4:
                        s = scenes[3]
                        v = s.get("visuals", [])
                        if v and v[0].get("type") == "text":
                            conclusion_text = v[0].get("content")

            except Exception as e:
                print(f"Failed to load screenplay from {screenplay_path}: {e}")

        # 1. Title Animation
        title = Text(title_text, font="Microsoft YaHei", font_size=48).to_edge(UP)
        self.play(Write(title))
        self.wait(1)

        # 2. Subtitle Animation
        subtitle = Text(subtitle_text, font="Microsoft YaHei", font_size=32).next_to(title, DOWN)
        self.play(Write(subtitle))
        self.wait(1)

        # 3. Features List
        # If features_list has only 1 item (from screenplay), center it
        if len(features_list) == 1:
             features = Text(features_list[0], font="Microsoft YaHei", font_size=32).to_edge(LEFT, buff=1)
        else:
            features = VGroup(
                *[Text(f, font="Microsoft YaHei", font_size=36) for f in features_list]
            ).arrange(DOWN, buff=0.5).to_edge(LEFT, buff=1)
        
        self.play(FadeIn(features, shift=RIGHT))
        self.wait(2)

        # 4. Image Placeholder (Dynamic Check)
        image_path = "assets/logo.png" # Example path
        if os.path.exists(image_path):
            image = ImageMobject(image_path).to_edge(RIGHT, buff=2)
            self.play(FadeIn(image, shift=LEFT))
            self.wait(2)
            self.play(FadeOut(image))
        else:
            # Fallback to a Shape
            placeholder = Square(color=BLUE, fill_opacity=0.5).to_edge(RIGHT, buff=2)
            label = Text(logo_label_text, font="Arial", font_size=24).move_to(placeholder)
            self.play(Create(placeholder), Write(label))
            self.wait(2)
            self.play(FadeOut(placeholder), FadeOut(label))

        # 5. Clear Features for Conclusion
        self.play(FadeOut(features), FadeOut(title), FadeOut(subtitle))
        
        # 6. Thank You Animation
        thank_you = Text(conclusion_text, font="Microsoft YaHei", font_size=64, color=YELLOW)
        self.play(Write(thank_you))
        self.play(Indicate(thank_you))
        self.wait(2)
