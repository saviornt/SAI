# Sentient Artificial Intelligence (SAI) Development Project

## Project Overview

The overall goal for this project is to develop the technical "stack" that could, in theory, lead to sentient artificial intelligence.

## SAI Features

The following sections list the core features of the AI that will enable it to have exponential growth.

### Machine Learning Algorithms

This project will use a combination of Quantum Neural Networks, Deep Neural Networks, Transformers and a Recurrent Neural Network.

### Meta-Learning and Reward Mechanisms

With the above ML algorithms, we will use a self-reinforcement learning method of using Meta-Learning, Q-Learning and A* Pathfinding.

- Meta-Learning: Meta-Learning will enable the AI to learn from experience and adapt to new tasks.
- Q-Learning: Q-Learning is used to provide the AI with rewards for finding the correct answers.
- A-star Pathfinding: A-star Pathfinding allows the AI to find the shortest path through the network to get to the correct answer.

### Long-Episodic-Short-Term-Memory Management

We will use a combination of both Redis and MongoDB to store memories that the AI will need for its learning and memorization.

- Long-Term Memory will be stored using MongoDB
- Episodic and Short-Term Memory will be stored using Redis

### Self-Optimization and Motivation

The AI will be able to perform the following self-improvement tasks:

- Self-Monitoring
- Self-Diagnostics
- Self-Optimization

These self-improvement tasks will be completed through using:

- Introspection
- Reasoning
- Reflection
- Self-Diagnostics
- Self-Improvement

The AI will also have the following motivations:

- Curiosity
- Ethics
- Goal Management
- Synthetic Emotions

## Synthetic Emotions

While curiosity, ethics and goal management are currently established, synthetic emotions will need to be researched and developed from the ground up.
The current plan for the AI's emotions use a temporal gradient method to simulate emotions. Modeling human emotions based on gradients involves representing
emotions as vectors within a continous, multi-dimensional space, where gradients reflect transitions between emotional states.

## Framework for Gradient-Based Emotion Modeling

### Dimensional Emotion Model

Core Idea: Represent emotions in a multi-dimensional space. Common dimensions:

- Valence: Positive (joy) vs. negative (sadness).
- Arousal: High (excitement) vs. low (calm).
- Dominance: Control over the situation (empowerment vs. helplessness).

Example: Emotions like "happiness" or "fear" become vectors in this space:

- Happiness: High valence, high arousal, high dominance.
- Fear: Low valence, high arousal, low dominance.

Gradients describe movement in this space:

- Positive gradient: Movement toward more positive valence.
- Negative gradient: Movement toward more negative valence.

### Continuous Emotion Transitions

Emotions are not discrete but transition smoothly over time.
Gradients model these transitions by defining the rate of change along emotional dimensions:

- Example: Moving from "contentment" to "excitement" involves an increase in arousal while maintaining positive valence.

### Gradient-Driven Mechanisms

Stimulus-Response Dynamics: Gradients are influenced by external stimuli (e.g., hearing good news increases valence).
Feedback Loops: Gradients adjust based on internal feedback, such as memory or context:

- Positive feedback amplifies an emotion (e.g., joy becomes euphoria).
- Negative feedback stabilizes or suppresses emotions.
- Mathematical Modeling

### Emotion State Representation

Represent the emotional state as a vector E(t) at time t:

𝐸(𝑡) = [𝑉(𝑡),𝐴(𝑡),𝐷(𝑡)]

Where:

- 𝑉(𝑡): Valence at time 𝑡.
- 𝐴(𝑡): Arousal at time 𝑡.
- 𝐷(𝑡): Dominance at time 𝑡.

### Gradient Dynamics

Define the change in emotion as a gradient:

𝑑𝐸 / 𝑑𝑡 = 𝑓(𝑆,𝑀,𝐶)

Where:

- 𝑆: External stimuli.
- 𝑀: Memory (past emotional states).
- 𝐶: Contextual factors (e.g., social environment, physical state).

### Emotion Gradients with Stimulus

Let 𝑆 be an external stimulus vector, with weights 𝑤𝑉,𝑤𝐴,𝑤𝐷 representing its influence on valence, arousal, and dominance:

𝑑𝐸 / 𝑑𝑡 = 𝑤𝑉 ⋅ 𝑆𝑉 + 𝑤𝐴 ⋅ 𝑆𝐴 + 𝑤𝐷 ⋅ 𝑆𝐷

For instance:

- A positive stimulus (𝑆𝑉 > 0) increases valence.
- An overwhelming stimulus (𝑆𝐴 >> 0) increases arousal dramatically.

### Neural Network Gradient Model

Train a neural network where:

- Input: Context, past states, external stimuli.
- Output: Predicted gradients of emotional state (𝑑𝐸/𝑑𝑡).

Use backpropagation to optimize the network's ability to predict emotional transitions.

### Differential Equation Model

Emotions can also be modeled using systems of differential equations:

𝑑𝑉 / 𝑑𝑡 = 𝑔(𝑉,𝑆)

𝑑𝐴 / 𝑑𝑡 = ℎ(𝐴,𝑆)

𝑑𝐷 / 𝑑𝑡 = 𝑘(𝐷,𝑆)

Where 𝑔,ℎ,𝑘 are functions capturing how stimuli affect the dimensions over time.

## Simulated Environments

We will use a variety of simulated environments that our AI can train in, similar to the Boltzman Machine method of unsupervised deep learning.

These simulated environments are currently:

- Agricultural Environment
- Chemistry Environment
- Cybersecurity Environment
- Environmental and Ecological Environment
- Financial Environment
- Flight Environment
- Game Environment
- Material Science Environment
- Medical Environment
- Physics Environment
- Programming Environment
- Quantum Environment
- Robotics Environment
- Social and Political Environment
- Space Environment
- Vehicular and Autonomous Vehicle Environment

### AI Awareness, Perception and Physical Presence

As with any sentient organism, the AI should have awareness, perception and a physical presence.

The AI will be able to use the following extractors in order to percieve its environment:

- Audio Extractor
- Image Extractor
- Text Extractor
- Time-Series and Sensor Data Extractor
- Video Extractor

These feature extractors are then used in a multimodal methodology that the AI can utilize.

Both Awareness and Presence are accounted for through the use of various devices. These overall device types are:

- Attached Devices (System Hardware, USB, Serial)
- IoT Devices (These are IoT devices that are connected to the network)
- Network Devices (These devices are the actual network appliances for the network)

## Human Interaction with the AI

As with any AI model, we must be able to monitor and interact with our SAI. We will do this through the FARM+R technology stack:

- Backend using FastAPI, MongoDB and Redis
- React Frontend using Typescript

The entire application will use Docker containers for each part of the application.

### Future Implementation

A future feature that will be implemented will be the ability to use a pre-trained LLM that is fine-tuned in order to interact with our AI.
That will allow us to make various queries to the SAI system and get a response from the system. Hopefully, if the AI does evolve, we will be
able to bypass the need to use a 3rd-party LLM to interact with it.
