## Project Overview

This project consists of the development of a 2D top-down farming environment in which a user controls a tractor to interact with crops distributed across an agricultural field. The system will initially be tested using mouse input and later integrated with a real haptic device to provide force feedback during interaction. The environment will include crop rows, obstacles, and different terrain conditions. Haptic feedback will simulate physical properties of the environment such as resistance at field boundaries, interaction forces with crops or objects, and variations in terrain stiffness or damping. The objective is to create an interactive task that allows us to study how haptic feedback influences navigation, task performance, and user experience.

## Task Distribution
1. **Environment Rendering and Crop Interaction**

Design and implement the visual representation of the agricultural field, including crop rows, plants, and obstacles. Develop the logic for crop placement and harvesting, as well as collision detection between the tractor and environmental elements. The environment should clearly indicate where the tractor should drive and what objects should be collected.

2. **Tractor Navigation and Gameplay Mechanics**

Implement the tractor movement and gameplay dynamics. This includes steering and navigation between crop rows, handling penalties when leaving the intended path, and managing the spawning and distribution of collectible items. The gameplay structure will define the scoring system and the conditions that determine the end of the task.

3. **Haptic Feedback and Control Implementation**

Develop the haptic interaction between the user and the environment. Implement force feedback representing environmental constraints such as row boundaries, terrain resistance, and object interaction using a stable spring–damper controller. The stiffness and damping parameters will be tuned to ensure stable and realistic haptic feedback.

## Evaluation

The performance of the system will be evaluated using metrics such as number of collected items, navigation accuracy, collisions with obstacles, and task completion time. These metrics will help analyze the effect of haptic feedback on user performance and interaction quality.